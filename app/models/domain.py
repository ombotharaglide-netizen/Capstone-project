"""Domain models for database persistence."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class LogEntry(Base):
    """Database model for log entries."""

    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(255), nullable=False, index=True)
    error_level = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    raw_log = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=True)
    embedding_id = Column(String(255), nullable=True, index=True)
    log_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<LogEntry(id={self.id}, service={self.service_name}, level={self.error_level})>"


class ResolutionHistory(Base):
    """Database model for resolution history."""

    __tablename__ = "resolution_history"

    id = Column(Integer, primary_key=True, index=True)
    log_entry_id = Column(Integer, nullable=False, index=True)
    root_cause = Column(Text, nullable=False)
    recommended_fix = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    similar_log_ids = Column(Text, nullable=True)  # JSON array string
    rag_context = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ResolutionHistory(id={self.id}, log_entry_id={self.log_entry_id}, confidence={self.confidence_score})>"
