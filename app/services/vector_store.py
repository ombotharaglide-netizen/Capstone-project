"""Vector store service using ChromaDB."""

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.exceptions import VectorStoreError
from app.core.logging import get_logger
from app.utils.helpers import safe_json_loads

logger = get_logger(__name__)


class VectorStore:
    """Service for managing vector storage and similarity search in ChromaDB."""

    def __init__(self, collection_name: str = "log_embeddings"):
        """
        Initialize vector store.

        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None

    @property
    def client(self) -> chromadb.ClientAPI:
        """Get or create ChromaDB client."""
        if self._client is None:
            try:
                logger.info(f"Initializing ChromaDB client with directory: {settings.chroma_persist_directory}")
                self._client = chromadb.PersistentClient(
                    path=settings.chroma_persist_directory,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                logger.info("ChromaDB client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB client: {e}")
                raise VectorStoreError(f"Failed to initialize ChromaDB client: {e}")
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create ChromaDB collection."""
        if self._collection is None:
            try:
                # Try to get existing collection or create new one
                try:
                    self._collection = self.client.get_collection(name=self.collection_name)
                    logger.info(f"Retrieved existing collection: {self.collection_name}")
                except Exception:
                    # Collection doesn't exist, create it
                    self._collection = self.client.create_collection(name=self.collection_name)
                    logger.info(f"Created new collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to get/create collection: {e}")
                raise VectorStoreError(f"Failed to get/create collection: {e}")
        return self._collection

    def add_embedding(
        self,
        embedding_id: str,
        embedding: List[float],
        document: str,
        log_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add embedding to vector store.

        Args:
            embedding_id: Unique identifier for the embedding
            embedding: Embedding vector
            document: Original document text
            log_metadata: Optional log metadata dictionary
        """
        try:
            # Prepare log metadata (ChromaDB requires string values)
            chroma_metadata: Dict[str, str] = {}
            if log_metadata:
                for key, value in log_metadata.items():
                    chroma_metadata[str(key)] = str(value)

            self.collection.add(
                ids=[embedding_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[chroma_metadata] if chroma_metadata else None,
            )
            logger.debug(f"Added embedding to vector store: {embedding_id}")
        except Exception as e:
            logger.error(f"Error adding embedding: {e}")
            raise VectorStoreError(f"Failed to add embedding: {e}")

    def query_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query similar embeddings.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of similar results with id, distance, document, and log metadata
        """
        try:
            # Prepare filter (ChromaDB requires string values)
            where: Optional[Dict[str, Any]] = None
            if filter_metadata:
                where = {str(k): str(v) for k, v in filter_metadata.items()}

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
            )

            # Format results
            formatted_results: List[Dict[str, Any]] = []
            if results["ids"] and len(results["ids"][0]) > 0:
                ids = results["ids"][0]
                distances = results["distances"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)

                for i in range(len(ids)):
                    formatted_results.append(
                        {
                            "id": ids[i],
                            "distance": distances[i],
                            "similarity": 1 - distances[i],  # Convert distance to similarity
                            "document": documents[i],
                            "log_metadata": metadatas[i] or {},
                        }
                    )

            logger.debug(f"Query returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying similar embeddings: {e}")
            raise VectorStoreError(f"Failed to query similar embeddings: {e}")

    def get_by_id(self, embedding_id: str) -> Optional[Dict[str, Any]]:
        """
        Get embedding by ID.

        Args:
            embedding_id: Embedding identifier

        Returns:
            Embedding data or None if not found
        """
        try:
            results = self.collection.get(ids=[embedding_id])
            if results["ids"] and len(results["ids"]) > 0:
                return {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "log_metadata": results["metadatas"][0] if results["metadatas"] else {},
                }
            return None
        except Exception as e:
            logger.warning(f"Error getting embedding by ID: {e}")
            return None

    def delete(self, embedding_id: str) -> None:
        """
        Delete embedding by ID.

        Args:
            embedding_id: Embedding identifier
        """
        try:
            self.collection.delete(ids=[embedding_id])
            logger.debug(f"Deleted embedding: {embedding_id}")
        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            raise VectorStoreError(f"Failed to delete embedding: {e}")

    def count(self) -> int:
        """
        Get total number of embeddings in collection.

        Returns:
            Count of embeddings
        """
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            logger.error(f"Error counting embeddings: {e}")
            raise VectorStoreError(f"Failed to count embeddings: {e}")


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
