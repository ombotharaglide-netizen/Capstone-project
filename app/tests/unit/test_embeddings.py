"""Unit tests for embedding service."""

import numpy as np
import pytest

from app.core.exceptions import EmbeddingError
from app.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

        embedding = service.generate_embedding("Test error message")

        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0
        assert embedding.dtype == np.float32

    def test_generate_embedding_empty_text(self):
        """Test embedding generation fails for empty text."""
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

        with pytest.raises(EmbeddingError):
            service.generate_embedding("")

    def test_generate_embeddings_batch(self):
        """Test batch embedding generation."""
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
        texts = [
            "Error: Connection timeout",
            "Warning: High memory usage",
            "Info: Request processed",
        ]

        embeddings = service.generate_embeddings(texts)

        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.dtype == np.float32 for emb in embeddings)

    def test_generate_embeddings_empty_list(self):
        """Test batch embedding generation with empty list."""
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

        embeddings = service.generate_embeddings([])

        assert embeddings == []

    def test_get_embedding_dimension(self):
        """Test getting embedding dimension."""
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

        dimension = service.get_embedding_dimension()

        assert dimension > 0
        assert isinstance(dimension, int)

    def test_similar_texts_have_similar_embeddings(self):
        """Test that similar texts produce similar embeddings."""
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

        text1 = "Connection timeout error"
        text2 = "Connection timeout occurred"
        text3 = "Database query failed"

        emb1 = service.generate_embedding(text1)
        emb2 = service.generate_embedding(text2)
        emb3 = service.generate_embedding(text3)

        # Calculate cosine similarity
        similarity_12 = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        similarity_13 = np.dot(emb1, emb3) / (np.linalg.norm(emb1) * np.linalg.norm(emb3))

        # Similar texts should have higher similarity
        assert similarity_12 > similarity_13
