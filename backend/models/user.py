from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def coerce_iso(v: Any) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


class UserDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fullName: str
    email: str
    password: str
    role: UserRole = UserRole.USER
    profileImage: Optional[str] = None
    createdAt: str = Field(default_factory=utc_now_iso)
    updatedAt: str = Field(default_factory=utc_now_iso)

    model_config = {"extra": "ignore"}

    @field_validator("createdAt", "updatedAt", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> str:
        return coerce_iso(v)


class UserPublic(BaseModel):
    id: str
    fullName: str
    email: str
    role: UserRole
    profileImage: Optional[str] = None
    createdAt: str
    updatedAt: str

    model_config = {"extra": "ignore"}

    @field_validator("createdAt", "updatedAt", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> str:
        return coerce_iso(v)


class ResetTokenDocument(BaseModel):
    userId: str
    tokenHash: str
    expiresAt: float  # Unix timestamp in milliseconds

    model_config = {"extra": "ignore"}

