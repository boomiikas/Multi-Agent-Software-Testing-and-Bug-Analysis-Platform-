import time
from typing import Tuple, Optional
from fastapi import HTTPException
from ..models.user import UserDocument, UserPublic, UserRole
from ..schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from ..repositories.user_repository import UserRepository
from ..security.passwords import hash_password, verify_password
from ..security.tokens import (
    sign_auth_token,
    generate_reset_token,
    hash_reset_token,
)
from ..config import settings


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, req: RegisterRequest) -> Tuple[str, UserPublic]:
        existing = await self.user_repo.find_by_email(req.email)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

        hashed = hash_password(req.password)
        new_user = UserDocument(
            fullName=req.fullName,
            email=req.email,
            password=hashed,
            role=UserRole.USER,
        )
        saved = await self.user_repo.create(new_user)
        token = sign_auth_token(saved.id, saved.email, saved.role.value)
        user_pub = UserPublic(**saved.model_dump())
        return token, user_pub

    async def login(self, req: LoginRequest) -> Tuple[str, UserPublic]:
        user = await self.user_repo.find_by_email(req.email)
        invalid_error = HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )
        if not user:
            raise invalid_error

        if not verify_password(req.password, user.password):
            raise invalid_error

        token = sign_auth_token(
            user.id,
            user.email,
            user.role.value,
            remember_me=bool(req.rememberMe),
        )
        user_pub = UserPublic(**user.model_dump())
        return token, user_pub

    async def forgot_password(self, email: str) -> Tuple[bool, str, Optional[str]]:
        user = await self.user_repo.find_by_email(email)
        message = "If that email is registered, a reset link has been sent."
        if not user:
            return True, message, None

        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        expires_at = (time.time() + settings.RESET_TOKEN_EXPIRES_IN_SECONDS) * 1000

        await self.user_repo.save_reset_token(user.id, token_hash, expires_at)

        dev_token = raw_token if settings.ENVIRONMENT != "production" else None
        return True, message, dev_token

    async def reset_password(self, req: ResetPasswordRequest) -> bool:
        token_hash = hash_reset_token(req.token)
        entry = await self.user_repo.find_reset_token(token_hash)
        now_ms = time.time() * 1000

        if not entry or entry.expiresAt < now_ms:
            raise HTTPException(
                status_code=400,
                detail="This reset link is invalid or has expired.",
            )

        hashed = hash_password(req.password)
        await self.user_repo.update(entry.userId, {"password": hashed})
        await self.user_repo.delete_reset_token(token_hash)
        return True

    async def change_password(self, user: UserDocument, req: ChangePasswordRequest) -> bool:
        if not verify_password(req.currentPassword, user.password):
            raise HTTPException(
                status_code=401,
                detail="Current password is incorrect.",
            )

        hashed = hash_password(req.password)
        await self.user_repo.update(user.id, {"password": hashed})
        return True
