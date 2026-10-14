from fastapi import APIRouter, Depends, status
from ..models.user import UserDocument, UserRole
from ..schemas.user import (
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    UserResponse,
    UsersListResponse,
)
from ..schemas.common import SuccessResponse
from ..repositories.user_repository import UserRepository, get_user_repository
from ..services.user_service import UserService
from ..security.dependencies import require_role

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo)


@router.get("/users", response_model=UsersListResponse)
async def list_users(user_service: UserService = Depends(get_user_service)):
    users = await user_service.list_all_users()
    return UsersListResponse(users=users)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: AdminUserCreateRequest,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.admin_create_user(req)
    return UserResponse(user=user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    req: AdminUserUpdateRequest,
    current_admin: UserDocument = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.admin_update_user(user_id, current_admin, req)
    return UserResponse(user=user)


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    current_admin: UserDocument = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.admin_delete_user(user_id, current_admin)
    return SuccessResponse(success=True)
