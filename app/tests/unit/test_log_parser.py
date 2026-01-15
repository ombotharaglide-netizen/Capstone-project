"""Unit tests for log parser service."""

import pytest

from app.core.exceptions import LogParsingError
from app.models.schemas import LogIngestionRequest, UnstructuredLogRequest
from app.services.log_parser import LogParser


class TestLogParser:
    """Test cases for LogParser service."""

    def test_parse_structured_log_success(self):
        """Test successful parsing of structured log."""
        parser = LogParser()
        request = LogIngestionRequest(
            service_name="api-service",
            error_level="ERROR",
            error_message="Connection timeout to database",
            raw_log="2024-01-01 10:00:00 ERROR api-service Connection timeout to database",
        )

        result = parser.parse_structured_log(request)

        assert result["service_name"] == "api-service"
        assert result["error_level"] == "ERROR"
        assert result["error_message"] == "Connection timeout to database"
        assert result["raw_log"] == request.raw_log
        assert result["normalized_text"] is not None
        assert len(result["normalized_text"]) > 0

    def test_parse_structured_log_with_metadata(self):
        """Test parsing structured log with metadata."""
        parser = LogParser()
        request = LogIngestionRequest(
            service_name="api-service",
            error_level="ERROR",
            error_message="Connection timeout",
            raw_log="Error log",
            log_metadata={"environment": "production", "version": "1.0.0"},
        )

        result = parser.parse_structured_log(request)

        assert result["log_metadata"] is not None
        assert "environment" in result["log_metadata"] or "production" in result["log_metadata"]

    def test_parse_unstructured_log_success(self):
        """Test successful parsing of unstructured log."""
        parser = LogParser()
        request = UnstructuredLogRequest(
            log_text="2024-01-01 10:00:00 ERROR [api-service] Connection timeout to database"
        )

        result = parser.parse_unstructured_log(request)

        assert result["service_name"] is not None
        assert result["error_level"] in ["ERROR", "WARN", "INFO", "DEBUG", "CRITICAL"]
        assert result["error_message"] is not None
        assert result["raw_log"] == request.log_text
        assert result["normalized_text"] is not None

    def test_parse_unstructured_log_with_service_name(self):
        """Test parsing unstructured log with provided service name."""
        parser = LogParser()
        request = UnstructuredLogRequest(
            log_text="Connection timeout to database",
            service_name="api-service",
        )

        result = parser.parse_unstructured_log(request)

        assert result["service_name"] == "api-service"

    def test_parse_log_text_convenience_method(self):
        """Test parse_log_text convenience method."""
        parser = LogParser()
        log_text = "ERROR Connection timeout"

        result = parser.parse_log_text(log_text)

        assert result["error_level"] == "ERROR"
        assert result["error_message"] is not None
        assert result["raw_log"] == log_text

    def test_normalize_log_entry(self, test_db_session):
        """Test normalizing log entry."""
        from app.models.domain import LogEntry

        parser = LogParser()
        log_entry = LogEntry(
            service_name="test-service",
            error_level="ERROR",
            error_message="Test error",
            raw_log="Test error",
        )

        normalized = parser.normalize_log_entry(log_entry)

        assert normalized.normalized_text is not None
        assert len(normalized.normalized_text) > 0
