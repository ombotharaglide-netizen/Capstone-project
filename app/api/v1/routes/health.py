"""Health check API routes."""

from datetime import datetime

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import HealthResponse
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Checks status of database, vector store, embedding service, and LLM service.
    """
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now(),
        "database": "unknown",
        "vector_store": "unknown",
        "embedding_service": "unknown",
        "llm_service": "unknown",
    }

    # Check database (basic check)
    try:
        from sqlalchemy import text
        from app.core.database import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check vector store
    try:
        vector_store = get_vector_store()
        count = vector_store.count()
        health_status["vector_store"] = f"healthy ({count} embeddings)"
    except Exception as e:
        logger.warning(f"Vector store health check failed: {e}")
        health_status["vector_store"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check embedding service
    try:
        embedding_service = get_embedding_service()
        test_embedding = embedding_service.generate_embedding("test")
        dim = len(test_embedding)
        health_status["embedding_service"] = f"healthy (dim={dim})"
    except Exception as e:
        logger.warning(f"Embedding service health check failed: {e}")
        health_status["embedding_service"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check LLM service (basic check - just verify API key is set)
    try:
        if settings.openrouter_api_key and settings.openrouter_api_key != "your_openrouter_api_key_here":
            health_status["llm_service"] = "configured"
        else:
            health_status["llm_service"] = "not_configured"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.warning(f"LLM service health check failed: {e}")
        health_status["llm_service"] = "unhealthy"
        health_status["status"] = "degraded"

    return HealthResponse(**health_status)
