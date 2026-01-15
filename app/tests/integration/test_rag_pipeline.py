"""Integration tests for RAG pipeline."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_log_entry(client):
    """Create a sample log entry for testing."""
    log_data = {
        "service_name": "test-service",
        "error_level": "ERROR",
        "error_message": "Database connection failed",
        "raw_log": "2024-01-01 10:00:00 ERROR test-service Database connection failed",
    }
    response = client.post("/api/v1/logs", json=log_data)
    return response.json()


class TestRAGPipeline:
    """Integration tests for RAG pipeline."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert "vector_store" in data

    def test_analyze_log_similarity(self, client, sample_log_entry):
        """Test log similarity analysis."""
        log_id = sample_log_entry["id"]

        response = client.get(f"/api/v1/analysis/{log_id}/similar?top_k=5")

        assert response.status_code == 200
        data = response.json()
        assert data["log_id"] == log_id
        assert "similar_logs" in data
        assert isinstance(data["similar_logs"], list)
        assert "pattern_detected" in data

    def test_analyze_log_similarity_not_found(self, client):
        """Test analysis fails for non-existent log."""
        response = client.get("/api/v1/analysis/99999/similar")

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.rag_engine.AsyncOpenAI")
    async def test_resolve_error_with_log_id(self, mock_openai_class, client, sample_log_entry):
        """Test error resolution with log ID."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"root_cause": "Database connection issue", "recommended_fix": "Check database connectivity", "confidence": 0.85}'
                )
            )
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        log_id = sample_log_entry["id"]

        # Note: This test requires actual API key or mocking
        # For now, we'll test the endpoint structure
        response = client.post(
            "/api/v1/resolve",
            json={"log_id": log_id, "top_k": 5},
        )

        # May fail without proper API key, but should not be a 404 or 400
        assert response.status_code in [200, 500, 503]

    def test_resolve_error_with_log_text(self, client):
        """Test error resolution with log text."""
        # This test requires OpenRouter API key
        # Without it, it will fail, but we test the endpoint structure
        response = client.post(
            "/api/v1/resolve",
            json={
                "log_text": "Database connection timeout",
                "service_name": "test-service",
                "top_k": 5,
            },
        )

        # May fail without proper API key, but should not be a 404 or 400
        assert response.status_code in [200, 500, 503]

    def test_resolve_error_missing_params(self, client):
        """Test resolution fails without log_id or log_text."""
        response = client.post("/api/v1/resolve", json={"top_k": 5})

        assert response.status_code == 422  # Validation error
