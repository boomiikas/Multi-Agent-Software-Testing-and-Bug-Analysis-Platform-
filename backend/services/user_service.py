from typing import List, Optional
from fastapi import HTTPException
from ..models.user import UserDocument, UserPublic, UserRole
from ..schemas.user import (
    ProfileUpdateRequest,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
)
from ..repositories.user_repository import UserRepository
from ..security.passwords import hash_password


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def update_profile(self, user: UserDocument, req: ProfileUpdateRequest) -> UserPublic:
        updates = {}
        if req.fullName is not None:
            updates["fullName"] = req.fullName
        if req.profileImage is not None:
            updates["profileImage"] = req.profileImage

        updated = await self.user_repo.update(user.id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found.")
        return UserPublic(**updated.model_dump())

    async def list_all_users(self) -> List[UserPublic]:
        users = await self.user_repo.find_all()
        return [UserPublic(**u.model_dump()) for u in users]

    async def admin_create_user(self, req: AdminUserCreateRequest) -> UserPublic:
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
            role=req.role,
        )
        saved = await self.user_repo.create(new_user)
        return UserPublic(**saved.model_dump())

    async def admin_update_user(
        self,
        target_id: str,
        current_admin: UserDocument,
        req: AdminUserUpdateRequest,
    ) -> UserPublic:
        target = await self.user_repo.find_by_id(target_id)
        if not target:
            raise HTTPException(status_code=404, detail="User not found.")

        updates = {}
        if req.fullName is not None:
            updates["fullName"] = req.fullName
        if req.email is not None:
            existing = await self.user_repo.find_by_email(req.email)
            if existing and existing.id != target_id:
                raise HTTPException(status_code=409, detail="Email already in use.")
            updates["email"] = req.email.lower()
        if req.role is not None:
            if target_id == current_admin.id and req.role != UserRole.ADMIN:
                raise HTTPException(status_code=400, detail="You cannot demote your own account.")
            updates["role"] = req.role
        if req.profileImage is not None:
            updates["profileImage"] = req.profileImage

        updated = await self.user_repo.update(target_id, updates)
        return UserPublic(**updated.model_dump())

    async def admin_delete_user(self, target_id: str, current_admin: UserDocument) -> bool:
        if target_id == current_admin.id:
            raise HTTPException(status_code=400, detail="You cannot delete your own account.")

        target = await self.user_repo.find_by_id(target_id)
        if not target:
            raise HTTPException(status_code=404, detail="User not found.")

        return await self.user_repo.delete(target_id)
