"""Error resolution API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import RAGError
from app.core.logging import get_logger
from app.models.domain import LogEntry
from app.models.schemas import (
    ErrorResponse,
    ResolutionRequest,
    ResolutionResponse,
    SimilarLog,
)
from app.services.resolver import get_resolver

logger = get_logger(__name__)

router = APIRouter(prefix="/resolve", tags=["resolution"])


@router.post(
    "",
    response_model=ResolutionResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def resolve_error(
    request: ResolutionRequest,
    db: Session = Depends(get_db),
) -> ResolutionResponse:
    """
    Resolve error using RAG pipeline.

    Accepts either a log_id (existing log) or log_text (ad-hoc resolution).
    """
    try:
        top_k = request.top_k or 5
        resolver = get_resolver()

        # --------------------------------------------------
        # CASE 1: Resolve existing log entry
        # --------------------------------------------------
        if request.log_id is not None:
            logger.info(f"Resolving error for log_id={request.log_id}")

            log_entry = (
                db.query(LogEntry)
                .filter(LogEntry.id == request.log_id)
                .first()
            )
            if not log_entry:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Log entry with id {request.log_id} not found",
                )

            resolution = await resolver.resolve_log_entry(
                log_entry,
                top_k=top_k,
                db_session=db,
            )

        # --------------------------------------------------
        # CASE 2: Ad-hoc resolution from log text
        # --------------------------------------------------
        elif request.log_text:
            logger.info("Resolving error from ad-hoc log text")

            resolution = await resolver.resolve_error(
                log_text=request.log_text,
                service_name=request.service_name,
                top_k=top_k,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either log_id or log_text must be provided",
            )

        # --------------------------------------------------
        # Build SimilarLog response objects
        # --------------------------------------------------
        similar_log_responses: List[SimilarLog] = []

        for log in resolution.get("similar_logs", []):
            log_id = log.get("id")
            similarity = log.get("similarity", 0.0)

            if not log_id:
                continue

            try:
                entry = (
                    db.query(LogEntry)
                    .filter(LogEntry.id == int(log_id))
                    .first()
                )
                if entry:
                    similar_log_responses.append(
                        SimilarLog(
                            id=entry.id,
                            service_name=entry.service_name,
                            error_level=entry.error_level,
                            error_message=entry.error_message,
                            similarity_score=similarity,
                            created_at=entry.created_at,
                        )
                    )
            except (ValueError, TypeError):
                continue

        logger.info("Successfully resolved error")

        # --------------------------------------------------
        # FINAL RESPONSE (MATCHES SCHEMA EXACTLY)
        # --------------------------------------------------
        return ResolutionResponse(
            log_id=resolution.get("log_entry_id", 0),
            root_cause=resolution["root_cause"],
            recommended_fix=resolution["recommended_fix"],
            confidence=resolution["confidence"],        # ✅ FIXED
            similar_logs=similar_log_responses,
            resolution_id=resolution.get("resolution_id"),
        )

    except HTTPException:
        raise

    except RAGError as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve error: {e}",
        )

    except Exception as e:
        logger.exception("Unexpected error resolving error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
