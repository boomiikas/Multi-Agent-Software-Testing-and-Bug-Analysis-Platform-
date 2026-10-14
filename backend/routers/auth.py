from fastapi import APIRouter, Depends, status
from ..schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    AuthResponse,
    ForgotPasswordResponse,
)
from ..schemas.user import UserResponse
from ..schemas.common import SuccessResponse
from ..models.user import UserDocument, UserPublic
from ..repositories.user_repository import UserRepository, get_user_repository
from ..services.auth_service import AuthService
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    token, user_pub = await auth_service.register(req)
    return AuthResponse(token=token, user=user_pub)


@router.post("/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    token, user_pub = await auth_service.login(req)
    return AuthResponse(token=token, user=user_pub, rememberMe=req.rememberMe)


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: UserDocument = Depends(get_current_user)):
    return SuccessResponse(success=True)


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserDocument = Depends(get_current_user)):
    return UserResponse(user=UserPublic(**current_user.model_dump()))


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    req: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    success, message, dev_token = await auth_service.forgot_password(req.email)
    return ForgotPasswordResponse(
        success=success,
        message=message,
        resetTokenForDev=dev_token,
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    req: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.reset_password(req)
    return SuccessResponse(
        success=True,
        message="Password has been reset. You can now log in.",
    )


@router.put("/change-password", response_model=SuccessResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: UserDocument = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.change_password(current_user, req)
    return SuccessResponse(
        success=True,
        message="Password updated successfully.",
    )
