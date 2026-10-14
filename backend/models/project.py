from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator


class ProjectStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def coerce_iso(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


class ProjectDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    targetUrl: str
    srsDocument: str = ""
    markdownSRS: Optional[str] = None
    ownerId: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PENDING
    totalRuns: int = 0
    passRate: Optional[float] = 0.0
    lastRunAt: Optional[str] = None
    createdAt: str = Field(default_factory=utc_now_iso)
    updatedAt: str = Field(default_factory=utc_now_iso)

    model_config = {"extra": "ignore"}

    @field_validator("createdAt", "updatedAt", "lastRunAt", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> Optional[str]:
        return coerce_iso(v)

    def model_post_init(self, __context: Any) -> None:
        if not self.markdownSRS and self.srsDocument:
            self.markdownSRS = self.srsDocument
        elif not self.srsDocument and self.markdownSRS:
            self.srsDocument = self.markdownSRS

