"""Integration tests for log ingestion API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_log_data():
    """Sample log data for testing."""
    return {
        "service_name": "test-service",
        "error_level": "ERROR",
        "error_message": "Connection timeout to database",
        "raw_log": "2024-01-01 10:00:00 ERROR test-service Connection timeout to database",
    }


class TestLogIngestionAPI:
    """Integration tests for log ingestion endpoints."""

    def test_ingest_structured_log_success(self, client, test_log_data):
        """Test successful ingestion of structured log."""
        response = client.post("/api/v1/logs", json=test_log_data)

        assert response.status_code == 201
        data = response.json()
        assert data["service_name"] == test_log_data["service_name"]
        assert data["error_level"] == test_log_data["error_level"]
        assert data["error_message"] == test_log_data["error_message"]
        assert data["id"] is not None
        assert data["embedding_id"] is not None

    def test_ingest_structured_log_with_metadata(self, client, test_log_data):
        """Test ingestion with metadata."""
        test_log_data["log_metadata"] = {"environment": "test", "version": "1.0.0"}

        response = client.post("/api/v1/logs", json=test_log_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None

    def test_ingest_unstructured_log_success(self, client):
        """Test successful ingestion of unstructured log."""
        log_data = {
            "log_text": "2024-01-01 10:00:00 ERROR [test-service] Connection timeout"
        }

        response = client.post("/api/v1/logs/unstructured", json=log_data)

        assert response.status_code == 201
        data = response.json()
        assert data["service_name"] is not None
        assert data["error_level"] is not None
        assert data["error_message"] is not None
        assert data["id"] is not None

    def test_ingest_log_invalid_error_level(self, client, test_log_data):
        """Test ingestion fails with invalid error level."""
        test_log_data["error_level"] = "INVALID_LEVEL"

        response = client.post("/api/v1/logs", json=test_log_data)

        assert response.status_code == 422  # Validation error

    def test_ingest_log_missing_required_fields(self, client):
        """Test ingestion fails with missing required fields."""
        incomplete_data = {
            "error_level": "ERROR",
            # Missing service_name and error_message
        }

        response = client.post("/api/v1/logs", json=incomplete_data)

        assert response.status_code == 422  # Validation error
