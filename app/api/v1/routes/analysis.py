"""Log analysis API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.models.domain import LogEntry
from app.models.schemas import AnalysisResponse, ErrorResponse, SimilarLog
from app.services.retriever import get_retriever

logger = get_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get(
    "/{log_id}/similar",
    response_model=AnalysisResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_log_similarity(
    log_id: int,
    top_k: int = Query(5, ge=1, le=20, description="Number of similar logs to retrieve"),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """
    Analyze log and find similar historical logs.

    Retrieves similar logs using vector similarity search.
    """
    try:
        logger.info(f"Analyzing log similarity for log_id: {log_id}")

        # Get log entry
        log_entry = db.query(LogEntry).filter(LogEntry.id == log_id).first()
        if not log_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log entry with id {log_id} not found",
            )

        # Retrieve similar logs
        retriever = get_retriever()
        query_text = log_entry.normalized_text or log_entry.error_message
        similar_results = retriever.retrieve_similar_logs(log_text=query_text, top_k=top_k + 1)

        # Format results and exclude current log
        similar_logs = retriever.format_retrieval_results(similar_results, exclude_id=log_id)
        similar_logs = similar_logs[:top_k]

        # Check for pattern (if similar logs found with high similarity)
        pattern_detected = len(similar_logs) > 0 and any(
            log.get("similarity", 0.0) > 0.7 for log in similar_logs
        )
        pattern_frequency = (
            len([log for log in similar_logs if log.get("similarity", 0.0) > 0.7])
            if pattern_detected
            else None
        )

        # Convert to response format
        similar_log_responses: List[SimilarLog] = []
        for log in similar_logs:
            # Try to get full log entry from database
            similar_log_id = log.get("id")
            if similar_log_id:
                try:
                    similar_entry = (
                        db.query(LogEntry)
                        .filter(LogEntry.id == int(similar_log_id))
                        .first()
                    )
                    if similar_entry:
                        similar_log_responses.append(
                            SimilarLog(
                                id=similar_entry.id,
                                service_name=similar_entry.service_name,
                                error_level=similar_entry.error_level,
                                error_message=similar_entry.error_message,
                                similarity_score=log.get("similarity", 0.0),
                                created_at=similar_entry.created_at,
                            )
                        )
                except (ValueError, TypeError):
                    pass

        logger.info(f"Found {len(similar_log_responses)} similar logs for log_id: {log_id}")

        return AnalysisResponse(
            log_id=log_id,
            similar_logs=similar_log_responses,
            pattern_detected=pattern_detected,
            pattern_frequency=pattern_frequency,
        )

    except HTTPException:
        raise
    except RetrievalError as e:
        logger.error(f"Retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve similar logs: {e.message}",
        )
    except Exception as e:
        logger.error(f"Unexpected error analyzing log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
