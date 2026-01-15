"""Custom exception classes for the application."""

from typing import Any, Optional


class LogErrorResolverException(Exception):
    """Base exception for all application-specific exceptions."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """Initialize exception with message and optional details."""
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(LogErrorResolverException):
    """Raised when there is a configuration error."""

    pass


class LogParsingError(LogErrorResolverException):
    """Raised when log parsing fails."""

    pass


class EmbeddingError(LogErrorResolverException):
    """Raised when embedding generation fails."""

    pass


class VectorStoreError(LogErrorResolverException):
    """Raised when vector store operations fail."""

    pass


class RetrievalError(LogErrorResolverException):
    """Raised when retrieval operations fail."""

    pass


class RAGError(LogErrorResolverException):
    """Raised when RAG pipeline operations fail."""

    pass


class LLMError(LogErrorResolverException):
    """Raised when LLM API calls fail."""

    pass


class DatabaseError(LogErrorResolverException):
    """Raised when database operations fail."""

    pass
