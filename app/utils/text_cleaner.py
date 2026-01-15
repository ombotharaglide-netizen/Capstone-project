"""Text cleaning and normalization utilities."""

import re
from typing import List

from app.core.logging import get_logger

logger = get_logger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for embedding generation.

    Removes:
    - Extra whitespace
    - Special characters (keeps alphanumeric, spaces, basic punctuation)
    - IP addresses (optional, replace with placeholder)
    - Timestamps (optional, replace with placeholder)
    - UUIDs (replace with placeholder)

    Args:
        text: Input text to normalize

    Returns:
        Normalized text string
    """
    if not text:
        return ""

    # Convert to lowercase
    normalized = text.lower()

    # Replace UUIDs with placeholder
    uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    normalized = re.sub(uuid_pattern, "<uuid>", normalized, flags=re.IGNORECASE)

    # Replace IP addresses with placeholder
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    normalized = re.sub(ip_pattern, "<ip>", normalized)

    # Replace long hex strings (like request IDs) with placeholder
    hex_pattern = r"\b[0-9a-f]{16,}\b"
    normalized = re.sub(hex_pattern, "<hex_id>", normalized, flags=re.IGNORECASE)

    # Replace timestamps (ISO format, Unix timestamp, etc.)
    iso_timestamp = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
    normalized = re.sub(iso_timestamp, "<timestamp>", normalized)

    unix_timestamp = r"\b\d{10}\.\d+\b"
    normalized = re.sub(unix_timestamp, "<timestamp>", normalized)

    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    return normalized


def extract_service_name(text: str) -> str:
    """
    Extract service name from log text using common patterns.

    Args:
        text: Log text to analyze

    Returns:
        Extracted service name or "unknown"
    """
    # Common patterns for service names in logs
    patterns = [
        r"service[=:]\s*([a-zA-Z0-9_-]+)",
        r"service_name[=:]\s*([a-zA-Z0-9_-]+)",
        r"\[([a-zA-Z0-9_-]+)\]",
        r"<([a-zA-Z0-9_-]+)>",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    # Try to find common service naming patterns
    service_keywords = ["api", "auth", "db", "cache", "worker", "scheduler", "web"]
    words = text.lower().split()
    for keyword in service_keywords:
        if keyword in words:
            idx = words.index(keyword)
            if idx > 0:
                return words[idx - 1] + "-" + keyword
            return keyword

    return "unknown"


def extract_error_level(text: str) -> str:
    """
    Extract error level from log text.

    Args:
        text: Log text to analyze

    Returns:
        Error level (ERROR, WARN, CRITICAL, etc.) or "INFO"
    """
    text_upper = text.upper()

    # Priority order: CRITICAL/FATAL > ERROR > WARN > INFO > DEBUG
    if any(keyword in text_upper for keyword in ["CRITICAL", "FATAL", "PANIC"]):
        return "CRITICAL"
    if "ERROR" in text_upper or "ERR" in text_upper:
        return "ERROR"
    if any(keyword in text_upper for keyword in ["WARN", "WARNING"]):
        return "WARN"
    if "DEBUG" in text_upper:
        return "DEBUG"
    if "INFO" in text_upper:
        return "INFO"

    return "INFO"  # Default


def extract_error_message(text: str, max_length: int = 500) -> str:
    """
    Extract error message from log text.

    Args:
        text: Log text to analyze
        max_length: Maximum length of extracted message

    Returns:
        Extracted error message
    """
    # Remove common log prefixes
    patterns_to_remove = [
        r"^\d{4}-\d{2}-\d{2}[^\s]*\s+",  # Date prefix
        r"^\[[^\]]+\]\s+",  # Bracket prefix
        r"^[A-Z]+\s+",  # Uppercase prefix (like ERROR, WARN)
    ]

    cleaned = text
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)

    # Take first meaningful line or truncate
    lines = cleaned.strip().split("\n")
    if lines:
        message = lines[0].strip()
        if len(message) > max_length:
            message = message[:max_length] + "..."
        return message

    return text[:max_length] if len(text) > max_length else text


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Input text

    Returns:
        List of tokens
    """
    # Simple tokenization (can be enhanced with NLTK/spaCy if needed)
    tokens = re.findall(r"\b\w+\b", text.lower())
    return tokens


def remove_stop_words(tokens: List[str]) -> List[str]:
    """
    Remove common stop words from tokens.

    Args:
        tokens: List of tokens

    Returns:
        Filtered list of tokens
    """
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
    }

    return [token for token in tokens if token not in stop_words]
