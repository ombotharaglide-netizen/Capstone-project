"""Application configuration management."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenRouter Configuration
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Application Configuration
    app_name: str = "Log Error Resolver"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database Configuration
    database_url: str = "sqlite:///./log_resolver.db"

    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"

    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # RAG Configuration
    top_k_similar_logs: int = 5
    max_context_length: int = 4000
    temperature: float = 0.3

    # API Configuration
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def openai_api_key(self) -> str:
        """Return OpenRouter API key for OpenAI client compatibility."""
        return self.openrouter_api_key

    @property
    def openai_base_url(self) -> str:
        """Return OpenRouter base URL for OpenAI client compatibility."""
        return self.openrouter_base_url


# Global settings instance
settings = Settings()
