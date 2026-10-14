from typing import Optional, Callable
from fastapi import Request, HTTPException, Depends
from ..models.user import UserDocument, UserRole
from ..repositories.user_repository import UserRepository, get_user_repository
from .tokens import verify_auth_token


async def get_current_user(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserDocument:
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Missing or malformed token.",
        )

    token = parts[1].strip()
    payload = verify_auth_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. User no longer exists.",
        )
    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    async def role_checker(current_user: UserDocument = Depends(get_current_user)) -> UserDocument:
        roles = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]
        user_role = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
        if user_role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You do not have permission to perform this action.",
            )
        return current_user

    return role_checker
