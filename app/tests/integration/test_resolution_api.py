"""Integration tests for error resolution API."""

from datetime import datetime
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import RAGError
from app.main import app
from app.models.domain import LogEntry


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_log_entry():
    """Create a mock log entry."""
    log_entry = LogEntry(
        id=1,
        service_name="test-service",
        error_level="ERROR",
        error_message="Connection timeout to database",
        raw_log="2024-01-01 10:00:00 ERROR test-service Connection timeout to database",
        normalized_text="ERROR test-service Connection timeout to database",
        embedding_id="test-embedding-id",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return log_entry


@pytest.fixture
def mock_resolution_response():
    """Create a mock resolution response from resolver."""
    return {
        "log_entry_id": 1,
        "root_cause": "Database connection pool exhausted",
        "recommended_fix": [
            "Increase database connection pool size",
            "Check for connection leaks",
            "Monitor connection usage",
        ],
        "confidence": 0.85,
        "similar_logs": [
            {"id": "2", "similarity": 0.92},
            {"id": "3", "similarity": 0.88},
        ],
        "resolution_id": 100,
    }


@pytest.fixture
def mock_resolution_response_ad_hoc():
    """Create a mock resolution response for ad-hoc resolution."""
    return {
        "log_entry_id": 0,
        "root_cause": "Network connectivity issue",
        "recommended_fix": [
            "Check network configuration",
            "Verify firewall rules",
        ],
        "confidence": 0.75,
        "similar_logs": [
            {"id": "5", "similarity": 0.90},
            {"id": "6", "similarity": 0.85},
        ],
    }


def setup_db_query_mocks(mock_db_session, main_log_entry=None, similar_logs=None):
    """Helper function to setup database query mocks."""
    similar_logs = similar_logs or []
    call_count = {"count": 0}

    def query_side_effect(model):
        call_count["count"] += 1
        query_mock = MagicMock()
        filter_mock = MagicMock()

        if main_log_entry is not None and call_count["count"] == 1:
            # First call for main log entry (only if main_log_entry is provided)
            filter_mock.first.return_value = main_log_entry
        else:
            # Calls for similar logs
            # If main_log_entry exists, similar logs start at call 2
            # If main_log_entry is None, similar logs start at call 1
            if main_log_entry is not None:
                log_idx = call_count["count"] - 2
            else:
                log_idx = call_count["count"] - 1
            
            if log_idx >= 0 and log_idx < len(similar_logs):
                filter_mock.first.return_value = similar_logs[log_idx]
            else:
                filter_mock.first.return_value = None

        query_mock.filter.return_value = filter_mock
        return query_mock

    mock_db_session.query.side_effect = query_side_effect


class TestResolutionAPI:
    """Integration tests for error resolution endpoints."""

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_with_log_id_success(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry, mock_resolution_response
    ):
        """Test successful resolution with existing log_id."""
        # Setup similar log entries
        similar_log_1 = LogEntry(
            id=2,
            service_name="test-service",
            error_level="ERROR",
            error_message="Database connection failed",
            raw_log="test log 2",
            created_at=datetime.now(),
        )
        similar_log_2 = LogEntry(
            id=3,
            service_name="test-service",
            error_level="ERROR",
            error_message="Connection pool exhausted",
            raw_log="test log 3",
            created_at=datetime.now(),
        )

        # Setup database mocks
        setup_db_query_mocks(mock_db_session, mock_log_entry, [similar_log_1, similar_log_2])

        # Setup resolver mock
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(return_value=mock_resolution_response)
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {"log_id": 1, "top_k": 5}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["log_id"] == 1
            assert data["root_cause"] == "Database connection pool exhausted"
            assert isinstance(data["recommended_fix"], list)
            assert len(data["recommended_fix"]) == 3
            assert data["confidence"] == 0.85
            assert data["resolution_id"] == 100
            assert isinstance(data["similar_logs"], list)
            assert len(data["similar_logs"]) == 2

            # Verify resolver was called correctly
            mock_resolver.resolve_log_entry.assert_called_once()
            call_args = mock_resolver.resolve_log_entry.call_args
            assert call_args[0][0] == mock_log_entry
            assert call_args[1]["top_k"] == 5
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_with_log_text_success(
        self, mock_get_resolver, client, mock_db_session, mock_resolution_response_ad_hoc
    ):
        """Test successful ad-hoc resolution with log_text."""
        # Create similar log entries
        similar_log_1 = LogEntry(
            id=5,
            service_name="api-service",
            error_level="ERROR",
            error_message="Network timeout",
            raw_log="test log 5",
            created_at=datetime.now(),
        )
        similar_log_2 = LogEntry(
            id=6,
            service_name="api-service",
            error_level="ERROR",
            error_message="Connection refused",
            raw_log="test log 6",
            created_at=datetime.now(),
        )

        # Setup database mocks
        setup_db_query_mocks(mock_db_session, None, [similar_log_1, similar_log_2])

        # Setup resolver mock
        mock_resolver = MagicMock()
        mock_resolver.resolve_error = AsyncMock(return_value=mock_resolution_response_ad_hoc)
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {
                "log_text": "2024-01-01 10:00:00 ERROR Network connection failed",
                "service_name": "api-service",
                "top_k": 5,
            }
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["log_id"] == 0
            assert data["root_cause"] == "Network connectivity issue"
            assert isinstance(data["recommended_fix"], list)
            assert len(data["recommended_fix"]) == 2
            assert data["confidence"] == 0.75
            assert isinstance(data["similar_logs"], list)
            assert len(data["similar_logs"]) == 2

            # Verify resolver was called correctly
            mock_resolver.resolve_error.assert_called_once()
            call_kwargs = mock_resolver.resolve_error.call_args[1]
            assert call_kwargs["log_text"] == "2024-01-01 10:00:00 ERROR Network connection failed"
            assert call_kwargs["service_name"] == "api-service"
            assert call_kwargs["top_k"] == 5
        finally:
            app.dependency_overrides.clear()

    def test_resolve_error_log_id_not_found(self, client, mock_db_session):
        """Test resolution fails when log_id doesn't exist."""
        # Setup database mocks - return None for log entry
        setup_db_query_mocks(mock_db_session, None, [])

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {"log_id": 999, "top_k": 5}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_resolve_error_missing_both_log_id_and_log_text(self, client):
        """Test resolution fails when neither log_id nor log_text is provided."""
        # Make request
        request_data = {"top_k": 5}
        response = client.post("/api/v1/resolve", json=request_data)

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "either log_id or log_text must be provided" in data["detail"].lower()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_rag_error(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry
    ):
        """Test resolution handles RAGError correctly."""
        # Setup database mocks
        setup_db_query_mocks(mock_db_session, mock_log_entry, [])

        # Setup resolver mock to raise RAGError
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(side_effect=RAGError("RAG pipeline failed"))
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {"log_id": 1, "top_k": 5}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 500
            data = response.json()
            assert "failed to resolve error" in data["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_general_exception(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry
    ):
        """Test resolution handles general exceptions correctly."""
        # Setup database mocks
        setup_db_query_mocks(mock_db_session, mock_log_entry, [])

        # Setup resolver mock to raise general exception
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {"log_id": 1, "top_k": 5}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 500
            data = response.json()
            assert "internal server error" in data["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_with_default_top_k(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry, mock_resolution_response
    ):
        """Test resolution uses default top_k when not provided."""
        # Setup database mocks
        setup_db_query_mocks(mock_db_session, mock_log_entry, [])

        # Setup resolver mock
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(return_value=mock_resolution_response)
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request without top_k
            request_data = {"log_id": 1}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 200
            # Verify resolver was called with default top_k (5)
            call_kwargs = mock_resolver.resolve_log_entry.call_args[1]
            assert call_kwargs["top_k"] == 5
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_similar_logs_without_id(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry, mock_resolution_response
    ):
        """Test resolution handles similar logs without id correctly."""
        # Create resolution response with similar log without id
        resolution_without_id = {
            **mock_resolution_response,
            "similar_logs": [
                {"id": "2", "similarity": 0.92},
                {"similarity": 0.88},  # Missing id
                {"id": "3", "similarity": 0.85},
            ],
        }

        # Setup similar log entries
        similar_log_2 = LogEntry(
            id=2,
            service_name="test-service",
            error_level="ERROR",
            error_message="Test error 2",
            raw_log="test log 2",
            created_at=datetime.now(),
        )
        similar_log_3 = LogEntry(
            id=3,
            service_name="test-service",
            error_level="ERROR",
            error_message="Test error 3",
            raw_log="test log 3",
            created_at=datetime.now(),
        )

        # Setup database mocks
        setup_db_query_mocks(mock_db_session, mock_log_entry, [similar_log_2, similar_log_3])

        # Setup resolver mock
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(return_value=resolution_without_id)
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {"log_id": 1, "top_k": 5}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            # Should only include logs with valid ids (2 and 3)
            assert len(data["similar_logs"]) == 2
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_similar_logs_invalid_id(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry, mock_resolution_response
    ):
        """Test resolution handles similar logs with invalid id correctly."""
        # Create resolution response with invalid id
        resolution_invalid_id = {
            **mock_resolution_response,
            "similar_logs": [
                {"id": "invalid", "similarity": 0.92},  # Invalid id
                {"id": "2", "similarity": 0.88},
            ],
        }

        # Setup similar log entry
        similar_log_2 = LogEntry(
            id=2,
            service_name="test-service",
            error_level="ERROR",
            error_message="Test error 2",
            raw_log="test log 2",
            created_at=datetime.now(),
        )

        # Setup database mocks - first query will fail for invalid id
        call_count = {"count": 0}

        def query_side_effect(model):
            call_count["count"] += 1
            query_mock = MagicMock()
            filter_mock = MagicMock()

            if call_count["count"] == 1:
                filter_mock.first.return_value = mock_log_entry
            elif call_count["count"] == 2:
                # First similar log query with invalid id - will raise ValueError when converting
                # The code catches ValueError/TypeError, so we simulate that by returning None
                filter_mock.first.return_value = None
            elif call_count["count"] == 3:
                filter_mock.first.return_value = similar_log_2
            else:
                filter_mock.first.return_value = None

            query_mock.filter.return_value = filter_mock
            return query_mock

        mock_db_session.query.side_effect = query_side_effect

        # Setup resolver mock
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(return_value=resolution_invalid_id)
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request
            request_data = {"log_id": 1, "top_k": 5}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            # Should handle invalid ids gracefully
            assert isinstance(data["similar_logs"], list)
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.routes.resolution.get_resolver")
    def test_resolve_error_custom_top_k(
        self, mock_get_resolver, client, mock_db_session, mock_log_entry, mock_resolution_response
    ):
        """Test resolution uses custom top_k value."""
        # Setup database mocks
        setup_db_query_mocks(mock_db_session, mock_log_entry, [])

        # Setup resolver mock
        mock_resolver = MagicMock()
        mock_resolver.resolve_log_entry = AsyncMock(return_value=mock_resolution_response)
        mock_get_resolver.return_value = mock_resolver

        # Override database dependency
        def override_get_db() -> Generator[Session, None, None]:
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Make request with custom top_k
            request_data = {"log_id": 1, "top_k": 10}
            response = client.post("/api/v1/resolve", json=request_data)

            # Assertions
            assert response.status_code == 200
            # Verify resolver was called with custom top_k
            call_kwargs = mock_resolver.resolve_log_entry.call_args[1]
            assert call_kwargs["top_k"] == 10
        finally:
            app.dependency_overrides.clear()
