import time
import secrets
import hashlib
import jwt
from fastapi import HTTPException
from ..config import settings


def sign_auth_token(user_id: str, email: str, role: str, remember_me: bool = False) -> str:
    now = int(time.time())
    duration = (
        settings.JWT_REMEMBER_EXPIRES_IN_SECONDS
        if remember_me
        else settings.JWT_EXPIRES_IN_SECONDS
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + duration,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_auth_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


def generate_reset_token() -> str:
    return secrets.token_hex(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
