"""Log parsing and normalization service."""

from typing import Dict, Optional

from app.core.exceptions import LogParsingError
from app.core.logging import get_logger
from app.models.domain import LogEntry
from app.models.schemas import LogIngestionRequest, UnstructuredLogRequest
from app.utils.helpers import safe_json_dumps
from app.utils.text_cleaner import (
    extract_error_level,
    extract_error_message,
    extract_service_name,
    normalize_text,
)

logger = get_logger(__name__)


class LogParser:
    """Service for parsing and normalizing logs."""

    def parse_structured_log(self, request: LogIngestionRequest) -> Dict[str, str]:
        """
        Parse structured log request.

        Args:
            request: Structured log ingestion request

        Returns:
            Dictionary with parsed log data
        """
        try:
            normalized = normalize_text(request.error_message)
            log_metadata_json = safe_json_dumps(request.log_metadata)

            return {
                "service_name": request.service_name,
                "error_level": request.error_level,
                "error_message": request.error_message,
                "raw_log": request.raw_log,
                "normalized_text": normalized,
                "log_metadata": log_metadata_json,
            }
        except Exception as e:
            logger.error(f"Error parsing structured log: {e}")
            raise LogParsingError(f"Failed to parse structured log: {e}")

    def parse_unstructured_log(self, request: UnstructuredLogRequest) -> Dict[str, str]:
        """
        Parse unstructured log text.

        Args:
            request: Unstructured log request

        Returns:
            Dictionary with parsed log data
        """
        try:
            log_text = request.log_text
            service_name = request.service_name or extract_service_name(log_text)
            error_level = extract_error_level(log_text)
            error_message = extract_error_message(log_text)
            normalized = normalize_text(error_message)
            log_metadata_json = safe_json_dumps(request.log_metadata)

            return {
                "service_name": service_name,
                "error_level": error_level,
                "error_message": error_message,
                "raw_log": log_text,
                "normalized_text": normalized,
                "log_metadata": log_metadata_json,
            }
        except Exception as e:
            logger.error(f"Error parsing unstructured log: {e}")
            raise LogParsingError(f"Failed to parse unstructured log: {e}")

    def parse_log_text(self, log_text: str, service_name: Optional[str] = None) -> Dict[str, str]:
        """
        Parse log text (convenience method).

        Args:
            log_text: Raw log text
            service_name: Optional service name

        Returns:
            Dictionary with parsed log data
        """
        request = UnstructuredLogRequest(log_text=log_text, service_name=service_name)
        return self.parse_unstructured_log(request)

    def normalize_log_entry(self, log_entry: LogEntry) -> LogEntry:
        """
        Normalize existing log entry (update normalized_text if missing).

        Args:
            log_entry: Log entry to normalize

        Returns:
            Updated log entry
        """
        if not log_entry.normalized_text:
            log_entry.normalized_text = normalize_text(log_entry.error_message)
            logger.debug(f"Normalized log entry {log_entry.id}")

        return log_entry
