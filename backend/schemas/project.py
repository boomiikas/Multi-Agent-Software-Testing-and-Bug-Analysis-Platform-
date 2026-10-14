import re
from typing import Optional, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator
from ..models.project import ProjectStatus, coerce_iso


def validate_target_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("Target URL is required.")
    
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Target URL must use http or https scheme.")
    
    if not parsed.netloc:
        raise ValueError("Target URL must include a valid host/domain.")
        
    # Disallow dangerous schemes or embedded scripts
    lower = url.lower()
    if "javascript:" in lower or "data:" in lower or "vbscript:" in lower:
        raise ValueError("Target URL contains unsafe protocol/content.")
        
    return url


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    targetUrl: str
    srsDocument: Optional[str] = ""
    markdownSRS: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Project name must be at least 3 characters.")
        return v

    @field_validator("targetUrl")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_target_url(v)

    def get_srs_content(self) -> str:
        return self.srsDocument or self.markdownSRS or ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=120)
    targetUrl: Optional[str] = None
    srsDocument: Optional[str] = None
    markdownSRS: Optional[str] = None
    status: Optional[ProjectStatus] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 3:
                raise ValueError("Project name must be at least 3 characters.")
        return v

    @field_validator("targetUrl")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_target_url(v)
        return v


class ProjectResponse(BaseModel):
    id: str
    name: str
    targetUrl: str
    srsDocument: str = ""
    markdownSRS: Optional[str] = None
    ownerId: Optional[str] = None
    status: str
    totalRuns: int = 0
    passRate: float = 0.0
    lastRunAt: Optional[str] = None
    createdAt: str
    updatedAt: str

    model_config = {"extra": "ignore"}

    @field_validator("createdAt", "updatedAt", "lastRunAt", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> Optional[str]:
        return coerce_iso(v)
