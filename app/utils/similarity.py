"""Similarity calculation utilities."""

import numpy as np
from numpy.typing import NDArray
from typing import List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


def cosine_similarity(vec1: NDArray[np.float32], vec2: NDArray[np.float32]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    if vec1.shape != vec2.shape:
        raise ValueError(f"Vectors must have the same shape: {vec1.shape} vs {vec2.shape}")

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def calculate_similarities(
    query_vector: NDArray[np.float32],
    candidate_vectors: List[NDArray[np.float32]],
) -> List[float]:
    """
    Calculate cosine similarities between query vector and candidate vectors.

    Args:
        query_vector: Query embedding vector
        candidate_vectors: List of candidate embedding vectors

    Returns:
        List of similarity scores
    """
    similarities = []
    for candidate in candidate_vectors:
        try:
            sim = cosine_similarity(query_vector, candidate)
            similarities.append(sim)
        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            similarities.append(0.0)

    return similarities


def find_top_k_similar(
    query_vector: NDArray[np.float32],
    candidate_vectors: List[NDArray[np.float32]],
    candidate_ids: List[int],
    k: int = 5,
) -> List[Tuple[int, float]]:
    """
    Find top K most similar vectors.

    Args:
        query_vector: Query embedding vector
        candidate_vectors: List of candidate embedding vectors
        candidate_ids: List of IDs corresponding to candidate vectors
        k: Number of top results to return

    Returns:
        List of tuples (id, similarity_score) sorted by similarity (descending)
    """
    if len(candidate_vectors) != len(candidate_ids):
        raise ValueError("candidate_vectors and candidate_ids must have the same length")

    similarities = calculate_similarities(query_vector, candidate_vectors)

    # Create list of (id, similarity) tuples
    results = list(zip(candidate_ids, similarities))

    # Sort by similarity (descending)
    results.sort(key=lambda x: x[1], reverse=True)

    # Return top K
    return results[:k]


def normalize_vector(vector: NDArray[np.float32]) -> NDArray[np.float32]:
    """
    Normalize vector to unit length.

    Args:
        vector: Input vector

    Returns:
        Normalized vector
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def batch_cosine_similarity(
    query_vectors: NDArray[np.float32], candidate_vectors: NDArray[np.float32]
) -> NDArray[np.float32]:
    """
    Calculate cosine similarity between batches of vectors (more efficient).

    Args:
        query_vectors: Query vectors (shape: [n_queries, dim])
        candidate_vectors: Candidate vectors (shape: [n_candidates, dim])

    Returns:
        Similarity matrix (shape: [n_queries, n_candidates])
    """
    # Normalize vectors
    query_norm = query_vectors / np.linalg.norm(query_vectors, axis=1, keepdims=True)
    candidate_norm = candidate_vectors / np.linalg.norm(candidate_vectors, axis=1, keepdims=True)

    # Matrix multiplication for batch similarity
    similarity_matrix = np.dot(query_norm, candidate_norm.T)

    return similarity_matrix
