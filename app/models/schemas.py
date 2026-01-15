"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ----------------------------------------------------------------------
# REQUEST SCHEMAS
# ----------------------------------------------------------------------

class LogIngestionRequest(BaseModel):
    """Schema for log ingestion request."""

    service_name: str = Field(..., description="Name of the service generating the log")
    error_level: str = Field(..., description="Error level (ERROR, WARN, CRITICAL, etc.)")
    error_message: str = Field(..., description="Error message text")
    raw_log: str = Field(..., description="Raw log text")
    log_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional log metadata"
    )

    @field_validator("error_level")
    @classmethod
    def validate_error_level(cls, v: str) -> str:
        valid_levels = ["ERROR", "WARN", "WARNING", "CRITICAL", "FATAL", "INFO", "DEBUG"]
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"error_level must be one of {valid_levels}")
        return upper_v


class UnstructuredLogRequest(BaseModel):
    """Schema for unstructured log ingestion request."""

    log_text: str = Field(..., description="Raw unstructured log text")
    service_name: Optional[str] = Field(None, description="Service name (if known)")
    log_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional log metadata"
    )


class ResolutionRequest(BaseModel):
    """Schema for resolution request."""

    log_id: Optional[int] = Field(None, description="ID of existing log entry")
    log_text: Optional[str] = Field(None, description="Log text for ad-hoc resolution")
    service_name: Optional[str] = Field(None, description="Service name")
    top_k: int = Field(5, ge=1, le=20, description="Number of similar logs to retrieve")


# ----------------------------------------------------------------------
# RESPONSE SCHEMAS
# ----------------------------------------------------------------------

class LogEntryResponse(BaseModel):
    """Schema for log entry response."""

    id: int
    service_name: str
    error_level: str
    error_message: str
    raw_log: str
    normalized_text: Optional[str] = None
    embedding_id: Optional[str] = None
    log_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimilarLog(BaseModel):
    """Schema for similar log entry."""

    id: int
    service_name: str
    error_level: str
    error_message: str
    similarity_score: float
    created_at: datetime


class ResolutionResponse(BaseModel):
    """Schema for resolution response."""

    log_id: int
    root_cause: str
    recommended_fix: List[str]          # ✅ FIXED
    confidence: float                   # ✅ FIXED
    similar_logs: List[SimilarLog]
    resolution_id: Optional[int] = None


class AnalysisResponse(BaseModel):
    """Schema for log analysis response."""

    log_id: int
    similar_logs: List[SimilarLog]
    pattern_detected: bool
    pattern_frequency: Optional[int] = None


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    version: str
    timestamp: datetime
    database: str
    vector_store: str
    embedding_service: str
    llm_service: str


class ErrorResponse(BaseModel):
    """Schema for error response."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
