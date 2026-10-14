import re
from typing import Optional, List
from pydantic import BaseModel, field_validator
from ..models.user import UserPublic, UserRole

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def sanitize_text(v: str) -> str:
    if not isinstance(v, str):
        return v
    return re.sub(r"[<>${}]", "", v).strip()


def validate_email_str(v: str) -> str:
    cleaned = sanitize_text(v).lower()
    if not cleaned or not EMAIL_RE.match(cleaned):
        raise ValueError("A valid email is required.")
    return cleaned


class ProfileUpdateRequest(BaseModel):
    fullName: Optional[str] = None
    profileImage: Optional[str] = None

    @field_validator("fullName")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = sanitize_text(v)
            if len(cleaned) < 2:
                raise ValueError("Full name must be at least 2 characters.")
            return cleaned
        return v


class AdminUserCreateRequest(BaseModel):
    fullName: str
    email: str
    password: str
    role: UserRole = UserRole.USER

    @field_validator("fullName")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        cleaned = sanitize_text(v)
        if len(cleaned) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_str(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class AdminUserUpdateRequest(BaseModel):
    fullName: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    profileImage: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_email_str(v)
        return v

    @field_validator("fullName")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = sanitize_text(v)
            if len(cleaned) < 2:
                raise ValueError("Full name must be at least 2 characters.")
            return cleaned
        return v


class UserResponse(BaseModel):
    user: UserPublic


class UsersListResponse(BaseModel):
    users: List[UserPublic]
