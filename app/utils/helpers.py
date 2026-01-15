"""Helper utility functions."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def safe_json_loads(json_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string to dictionary.

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed dictionary or None if parsing fails
    """
    if not json_str:
        return None

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return None


def safe_json_dumps(data: Any) -> Optional[str]:
    """
    Safely serialize data to JSON string.

    Args:
        data: Data to serialize

    Returns:
        JSON string or None if serialization fails
    """
    if data is None:
        return None

    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize JSON: {e}")
        return None


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to ISO string.

    Args:
        dt: Datetime object

    Returns:
        ISO formatted string
    """
    return dt.isoformat()


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parse ISO datetime string.

    Args:
        dt_str: ISO datetime string

    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse datetime: {e}")
        return None


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries (later dicts override earlier ones).

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def extract_patterns(text: str) -> Dict[str, list[str]]:
    """
    Extract common patterns from text (URLs, emails, etc.).

    Args:
        text: Text to analyze

    Returns:
        Dictionary of pattern types and matches
    """
    import re

    patterns: Dict[str, list[str]] = {
        "urls": [],
        "emails": [],
        "ip_addresses": [],
        "uuids": [],
    }

    # URLs
    url_pattern = r"https?://[^\s]+"
    patterns["urls"] = re.findall(url_pattern, text)

    # Emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    patterns["emails"] = re.findall(email_pattern, text)

    # IP addresses
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    patterns["ip_addresses"] = re.findall(ip_pattern, text)

    # UUIDs
    uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    patterns["uuids"] = re.findall(uuid_pattern, text, re.IGNORECASE)

    return patterns
