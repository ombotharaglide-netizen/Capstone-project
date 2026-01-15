"""Log ingestion API routes."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DatabaseError, LogParsingError
from app.core.logging import get_logger
from app.models.schemas import (
    ErrorResponse,
    LogEntryResponse,
    LogIngestionRequest,
    UnstructuredLogRequest,
)
from app.services.log_parser import LogParser
from app.services.resolver import get_resolver

logger = get_logger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


def _normalize_metadata(metadata):
    """
    Ensure log_metadata is always returned as a dict.
    SQLite may return JSON as string.
    """
    if metadata is None:
        return {}
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    return metadata


@router.post(
    "",
    response_model=LogEntryResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def ingest_log(
    request: LogIngestionRequest,
    db: Session = Depends(get_db),
) -> LogEntryResponse:
    """
    Ingest structured log entry.
    """
    try:
        logger.info(f"Ingesting structured log for service: {request.service_name}")

        # Parse log
        parser = LogParser()
        parsed = parser.parse_structured_log(request)

        # Store log + embedding
        resolver = get_resolver()
        log_entry = resolver.store_log_with_embedding(parsed, db)

        logger.info(f"Successfully ingested log entry: {log_entry.id}")

        return LogEntryResponse(
            id=log_entry.id,
            service_name=log_entry.service_name,
            error_level=log_entry.error_level,
            error_message=log_entry.error_message,
            raw_log=log_entry.raw_log,
            normalized_text=log_entry.normalized_text,
            embedding_id=log_entry.embedding_id,
            log_metadata=_normalize_metadata(log_entry.log_metadata),
            created_at=log_entry.created_at,
            updated_at=log_entry.updated_at,
        )

    except LogParsingError as e:
        logger.error(f"Log parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse log: {e.message}",
        )

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store log: {e.message}",
        )

    except Exception as e:
        logger.exception("Unexpected error ingesting log")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/unstructured",
    response_model=LogEntryResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def ingest_unstructured_log(
    request: UnstructuredLogRequest,
    db: Session = Depends(get_db),
) -> LogEntryResponse:
    """
    Ingest unstructured log entry.
    """
    try:
        logger.info("Ingesting unstructured log")

        # Parse unstructured log
        parser = LogParser()
        parsed = parser.parse_unstructured_log(request)

        # Store log + embedding
        resolver = get_resolver()
        log_entry = resolver.store_log_with_embedding(parsed, db)

        logger.info(f"Successfully ingested unstructured log entry: {log_entry.id}")

        return LogEntryResponse(
            id=log_entry.id,
            service_name=log_entry.service_name,
            error_level=log_entry.error_level,
            error_message=log_entry.error_message,
            raw_log=log_entry.raw_log,
            normalized_text=log_entry.normalized_text,
            embedding_id=log_entry.embedding_id,
            log_metadata=_normalize_metadata(log_entry.log_metadata),
            created_at=log_entry.created_at,
            updated_at=log_entry.updated_at,
        )

    except LogParsingError as e:
        logger.error(f"Log parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse log: {e.message}",
        )

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store log: {e.message}",
        )

    except Exception as e:
        logger.exception("Unexpected error ingesting unstructured log")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
