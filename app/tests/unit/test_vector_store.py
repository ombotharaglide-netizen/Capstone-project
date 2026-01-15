"""Unit tests for vector store service."""

import pytest

from app.core.exceptions import VectorStoreError
from app.services.vector_store import VectorStore


class TestVectorStore:
    """Test cases for VectorStore service."""

    @pytest.fixture
    def vector_store(self, cleanup_test_chroma_db):
        """Create vector store instance for testing."""
        return VectorStore(collection_name="test_collection")

    def test_add_embedding_success(self, vector_store):
        """Test successfully adding embedding to vector store."""
        embedding_id = "test_1"
        embedding = [0.1] * 384  # Dummy embedding vector
        document = "Test error message"

        vector_store.add_embedding(
            embedding_id=embedding_id,
            embedding=embedding,
            document=document,
        )

        # Verify embedding was added
        result = vector_store.get_by_id(embedding_id)
        assert result is not None
        assert result["id"] == embedding_id
        assert result["document"] == document

    def test_add_embedding_with_metadata(self, vector_store):
        """Test adding embedding with log metadata."""
        embedding_id = "test_2"
        embedding = [0.2] * 384
        document = "Test error message with log metadata"
        log_metadata = {"environment": "production", "version": "1.0.0"}

        vector_store.add_embedding(
            embedding_id=embedding_id,
            embedding=embedding,
            document=document,
            log_metadata=log_metadata,
        )

        result = vector_store.get_by_id(embedding_id)
        assert result is not None
        assert result["log_metadata"]["environment"] == "production"
        assert result["log_metadata"]["version"] == "1.0.0"

    def test_query_similar_embeddings(self, vector_store):
        """Test querying similar embeddings."""
        # Add multiple embeddings
        embeddings = [
            ([0.1] * 384, "test_1", "Error: Connection timeout"),
            ([0.2] * 384, "test_2", "Error: Database connection failed"),
            ([0.9] * 384, "test_3", "Info: Request processed"),  # Different type
        ]

        for embedding, emb_id, doc in embeddings:
            vector_store.add_embedding(
                embedding_id=emb_id,
                embedding=embedding,
                document=doc,
            )

        # Query with similar embedding
        query_embedding = [0.15] * 384
        results = vector_store.query_similar(query_embedding=query_embedding, top_k=2)

        assert len(results) > 0
        assert all("id" in result for result in results)
        assert all("similarity" in result for result in results)
        assert all("document" in result for result in results)

    def test_get_by_id_not_found(self, vector_store):
        """Test getting non-existent embedding."""
        result = vector_store.get_by_id("non_existent_id")

        assert result is None

    def test_delete_embedding(self, vector_store):
        """Test deleting embedding."""
        embedding_id = "test_delete"
        embedding = [0.3] * 384
        document = "Test document to delete"

        vector_store.add_embedding(
            embedding_id=embedding_id,
            embedding=embedding,
            document=document,
        )

        # Verify it exists
        assert vector_store.get_by_id(embedding_id) is not None

        # Delete it
        vector_store.delete(embedding_id)

        # Verify it's gone
        assert vector_store.get_by_id(embedding_id) is None

    def test_count_embeddings(self, vector_store):
        """Test counting embeddings in collection."""
        initial_count = vector_store.count()

        # Add some embeddings
        for i in range(3):
            vector_store.add_embedding(
                embedding_id=f"count_test_{i}",
                embedding=[0.1] * 384,
                document=f"Test document {i}",
            )

        new_count = vector_store.count()
        assert new_count == initial_count + 3
