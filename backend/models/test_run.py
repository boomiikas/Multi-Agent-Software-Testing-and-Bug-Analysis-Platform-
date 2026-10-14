from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def coerce_iso(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


class TestRunDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    projectId: str
    status: RunStatus = RunStatus.PENDING
    agent: str = "TestMaster-v3"
    currentStage: Optional[str] = None
    stepsCompleted: int = 0
    totalSteps: int = 9
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    errorTrace: Optional[str] = None
    report: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    stageTimings: Dict[str, float] = Field(default_factory=dict)
    findings: Dict[str, Any] = Field(default_factory=dict)
    apiExecution: Optional[Dict[str, Any]] = None
    securityExecution: Optional[Dict[str, Any]] = None
    rcaDiagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    retryHistory: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    cancelled: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)
    duration: Optional[int] = None
    startTime: str = Field(default_factory=utc_now_iso)
    endTime: Optional[str] = None
    createdAt: str = Field(default_factory=utc_now_iso)

    model_config = {"extra": "ignore"}

    @field_validator("createdAt", "startTime", "endTime", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> Optional[str]:
        return coerce_iso(v)

