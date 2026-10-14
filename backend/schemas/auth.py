import re
from typing import Optional
from pydantic import BaseModel, field_validator
from ..models.user import UserPublic

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


class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str

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
        if not re.search(r"[A-Z]", v) or not re.search(r"[0-9]", v):
            raise ValueError("Password must include at least one uppercase letter and one number.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_str(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required.")
        return v


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_str(v)


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Reset token is required.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v) or not re.search(r"[0-9]", v):
            raise ValueError("Password must include at least one uppercase letter and one number.")
        return v


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v) or not re.search(r"[0-9]", v):
            raise ValueError("Password must include at least one uppercase letter and one number.")
        return v


class AuthResponse(BaseModel):
    token: str
    user: UserPublic
    rememberMe: Optional[bool] = False


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str = "If that email is registered, a reset link has been sent."
    resetTokenForDev: Optional[str] = None
