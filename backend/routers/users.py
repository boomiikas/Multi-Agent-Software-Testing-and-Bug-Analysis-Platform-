from fastapi import APIRouter, Depends
from ..schemas.user import ProfileUpdateRequest, UserResponse
from ..models.user import UserDocument, UserPublic
from ..repositories.user_repository import UserRepository, get_user_repository
from ..services.user_service import UserService
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo)


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: UserDocument = Depends(get_current_user)):
    return UserResponse(user=UserPublic(**current_user.model_dump()))


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: UserDocument = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    updated = await user_service.update_profile(current_user, req)
    return UserResponse(user=updated)
