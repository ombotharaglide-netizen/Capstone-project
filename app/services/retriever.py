"""Retriever service for finding similar historical logs."""

from typing import Any, List, Optional

from app.core.config import settings
from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.models.domain import LogEntry
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store
from app.utils.helpers import safe_json_loads

logger = get_logger(__name__)


class Retriever:
    """Service for retrieving similar historical logs."""

    def __init__(self):
        """Initialize retriever with dependencies."""
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    def retrieve_similar_logs(
        self,
        log_text: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[dict] = None,
    ) -> List[dict]:
        """
        Retrieve similar historical logs.

        Args:
            log_text: Log text to find similar logs for
            top_k: Number of similar logs to retrieve
            filter_metadata: Optional logmetadata filters

        Returns:
            List of similar log results with id, similarity, document, and log metadata
        """
        try:
            top_k = top_k or settings.top_k_similar_logs

            # Generate embedding for query text
            normalized_text = log_text
            query_embedding = self.embedding_service.generate_embedding(normalized_text)
            embedding_list = query_embedding.tolist()

            # Query vector store
            results = self.vector_store.query_similar(
                query_embedding=embedding_list,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )

            logger.info(f"Retrieved {len(results)} similar logs for query")
            return results
        except Exception as e:
            logger.error(f"Error retrieving similar logs: {e}")
            raise RetrievalError(f"Failed to retrieve similar logs: {e}")

    def retrieve_similar_by_log_id(
        self, log_entry_id: int, top_k: Optional[int] = None, db_session: Optional[Any] = None
    ) -> List[dict]:
        """
        Retrieve similar logs for an existing log entry.

        Args:
            log_entry_id: ID of the log entry
            top_k: Number of similar logs to retrieve
            db_session: Optional database session (if using SQLAlchemy)

        Returns:
            List of similar log results
        """
        # This method would require database access to get the log entry
        # For now, we'll raise an error indicating it needs to be implemented
        # with proper database session handling
        raise NotImplementedError(
            "This method requires database session. Use retrieve_similar_logs with log text instead."
        )

    def format_retrieval_results(
        self, results: List[dict], exclude_id: Optional[int] = None
    ) -> List[dict]:
        """
        Format retrieval results for RAG context.

        Args:
            results: Raw retrieval results from vector store
            exclude_id: Optional log entry ID to exclude from results

        Returns:
            Formatted results
        """
        formatted = []
        for result in results:
            log_metadata = result.get("log_metadata", {})
            log_id = log_metadata.get("log_id")

            # Skip excluded ID
            if exclude_id and log_id and str(log_id) == str(exclude_id):
                continue

            formatted.append(
                {
                    "id": log_id or result.get("id"),
                    "similarity": result.get("similarity", 0.0),
                    "document": result.get("document", ""),
                    "service_name": log_metadata.get("service_name", "unknown"),
                    "error_level": log_metadata.get("error_level", "UNKNOWN"),
                    "error_message": log_metadata.get("error_message", ""),
                }
            )

        return formatted


# Global retriever instance
_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Get global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
