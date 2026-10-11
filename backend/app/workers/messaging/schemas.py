import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobState(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    DLQ_FAILED = "DLQ_FAILED"


class MessagePayload(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    payload: Dict[str, Any]
    attempts: int = 0
    max_attempts: int = 3
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class RetryHistoryEntry(BaseModel):
    attempt: int
    timestamp: str
    error_type: str
    error_message: str
    backoff_seconds: float
    stack_trace: Optional[str] = None


class JobExecutionTracker(BaseModel):
    job_id: str
    topic: str
    state: JobState
    attempts: int = 0
    max_attempts: int = 3
    first_attempt_at: Optional[str] = None
    last_attempt_at: Optional[str] = None
    next_retry_at: Optional[str] = None
    last_error: Optional[str] = None
    history: List[RetryHistoryEntry] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)


class DLQItem(BaseModel):
    dlq_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_job_id: str
    topic: str
    payload: Dict[str, Any]
    failed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_attempts: int
    final_error: str
    error_type: str
    history: List[RetryHistoryEntry] = Field(default_factory=list)


class QueueMetrics(BaseModel):
    backend: str
    topic: str
    active_jobs: int = 0
    retry_jobs: int = 0
    dlq_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
