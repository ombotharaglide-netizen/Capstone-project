"""Resolver service - orchestration layer for error resolution."""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError, RAGError
from app.core.logging import get_logger
from app.models.domain import LogEntry, ResolutionHistory
from app.services.embedding_service import get_embedding_service
from app.services.log_parser import LogParser
from app.services.rag_engine import get_rag_engine
from app.services.retriever import get_retriever
from app.services.vector_store import get_vector_store
from app.utils.helpers import safe_json_dumps

logger = get_logger(__name__)


class Resolver:
    """Service for orchestrating error resolution using RAG."""

    def __init__(self) -> None:
        """Initialize resolver with dependencies."""
        self.log_parser = LogParser()
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.retriever = get_retriever()
        self.rag_engine = get_rag_engine()

    # ------------------------------------------------------------------
    # INTERNAL NORMALIZATION HELPERS
    # ------------------------------------------------------------------

    def _normalize_recommended_fix(self, recommended_fix: Any) -> List[str]:
        """
        Normalize recommended_fix into a list of strings.

        Handles:
        - single string
        - list of strings
        - multiline / bullet responses
        """
        if not recommended_fix:
            return []

        if isinstance(recommended_fix, list):
            return [str(item).strip() for item in recommended_fix if str(item).strip()]

        if isinstance(recommended_fix, str):
            lines = [
                line.strip(" -•\t")
                for line in recommended_fix.splitlines()
                if line.strip()
            ]
            return lines if lines else [recommended_fix.strip()]

        return [str(recommended_fix)]

    # ------------------------------------------------------------------
    # RAG RESOLUTION (ON-THE-FLY LOG TEXT)
    # ------------------------------------------------------------------

    async def resolve_error(
        self,
        log_text: str,
        service_name: Optional[str] = None,
        top_k: int = 5,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Resolve error using RAG pipeline for raw log text.
        """
        try:
            # Parse log
            parsed = self.log_parser.parse_log_text(log_text, service_name)
            error_message = parsed["error_message"]
            normalized_text = parsed["normalized_text"]

            # Retrieve similar logs
            similar_results = self.retriever.retrieve_similar_logs(
                log_text=normalized_text,
                top_k=top_k,
            )
            similar_logs = self.retriever.format_retrieval_results(similar_results)

            # Generate resolution via RAG
            resolution = await self.rag_engine.generate_resolution(
                error_message=error_message,
                similar_logs=similar_logs,
                context=f"Service: {parsed['service_name']}, Level: {parsed['error_level']}",
            )

            normalized_fix = self._normalize_recommended_fix(
                resolution.get("recommended_fix")
            )

            return {
                "error_message": error_message,
                "service_name": parsed["service_name"],
                "error_level": parsed["error_level"],
                "root_cause": resolution["root_cause"],
                "recommended_fix": normalized_fix,
                "confidence": resolution["confidence"],
                "similar_logs": similar_logs,
            }

        except Exception as e:
            logger.exception("Error resolving error")
            raise RAGError(f"Failed to resolve error: {e}")

    # ------------------------------------------------------------------
    # RAG RESOLUTION (EXISTING LOG ENTRY)
    # ------------------------------------------------------------------

    async def resolve_log_entry(
        self,
        log_entry: LogEntry,
        top_k: int = 5,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Resolve error for an existing log entry.
        """
        try:
            query_text = log_entry.normalized_text or log_entry.error_message

            # Retrieve similar logs (exclude current log)
            similar_results = self.retriever.retrieve_similar_logs(
                log_text=query_text,
                top_k=top_k + 1,
            )
            similar_logs = self.retriever.format_retrieval_results(
                similar_results,
                exclude_id=log_entry.id,
            )[:top_k]

            # Generate resolution
            resolution = await self.rag_engine.generate_resolution(
                error_message=log_entry.error_message,
                similar_logs=similar_logs,
                context=f"Service: {log_entry.service_name}, Level: {log_entry.error_level}",
            )

            normalized_fix = self._normalize_recommended_fix(
                resolution.get("recommended_fix")
            )

            resolution_id = None
            if db_session:
                try:
                    resolution_record = ResolutionHistory(
                        log_entry_id=log_entry.id,
                        root_cause=resolution["root_cause"],
                        recommended_fix=safe_json_dumps(normalized_fix),
                        confidence_score=resolution["confidence"],
                        similar_log_ids=safe_json_dumps(
                            [log.get("id") for log in similar_logs if log.get("id")]
                        ),
                        rag_context=safe_json_dumps(
                            {"similar_logs_count": len(similar_logs), "top_k": top_k}
                        ),
                    )
                    db_session.add(resolution_record)
                    db_session.commit()
                    db_session.refresh(resolution_record)
                    resolution_id = resolution_record.id
                except Exception as e:
                    logger.error(f"Failed to store resolution: {e}")
                    db_session.rollback()

            return {
                "log_entry_id": log_entry.id,
                "error_message": log_entry.error_message,
                "service_name": log_entry.service_name,
                "error_level": log_entry.error_level,
                "root_cause": resolution["root_cause"],
                "recommended_fix": normalized_fix,
                "confidence": resolution["confidence"],
                "similar_logs": similar_logs,
                "resolution_id": resolution_id,
            }

        except Exception as e:
            logger.exception("Error resolving log entry")
            raise RAGError(f"Failed to resolve log entry: {e}")

    # ------------------------------------------------------------------
    # LOG STORAGE + EMBEDDING
    # ------------------------------------------------------------------

    def store_log_with_embedding(
        self,
        parsed_log: Dict[str, Any],
        db_session: Session,
        embedding_id: Optional[str] = None,
    ) -> LogEntry:
        """
        Store log entry and generate/store embedding.
        """
        try:
            log_entry = LogEntry(
                service_name=parsed_log["service_name"],
                error_level=parsed_log["error_level"],
                error_message=parsed_log["error_message"],
                raw_log=parsed_log["raw_log"],
                normalized_text=parsed_log["normalized_text"],
                log_metadata=parsed_log.get("log_metadata"),
            )
            db_session.add(log_entry)
            db_session.commit()
            db_session.refresh(log_entry)

            if not embedding_id:
                embedding_id = f"log_{log_entry.id}"

            embedding = self.embedding_service.generate_embedding(
                parsed_log["normalized_text"]
            ).tolist()

            self.vector_store.add_embedding(
                embedding_id=embedding_id,
                embedding=embedding,
                document=parsed_log["normalized_text"],
                log_metadata={
                    "log_id": str(log_entry.id),
                    "service_name": parsed_log["service_name"],
                    "error_level": parsed_log["error_level"],
                },
            )

            log_entry.embedding_id = embedding_id
            db_session.commit()
            db_session.refresh(log_entry)

            logger.info(f"Stored log entry {log_entry.id} with embedding {embedding_id}")
            return log_entry

        except Exception as e:
            logger.error(f"Error storing log with embedding: {e}")
            db_session.rollback()
            raise DatabaseError(f"Failed to store log with embedding: {e}")


# ----------------------------------------------------------------------
# GLOBAL RESOLVER INSTANCE
# ----------------------------------------------------------------------

_resolver: Optional[Resolver] = None


def get_resolver() -> Resolver:
    """Get singleton resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = Resolver()
    return _resolver
