from loguru import logger
from .config import settings
from .models.user import UserDocument, UserRole
from .repositories.user_repository import UserRepository
from .security.passwords import hash_password
from .database import is_mongo_connected


async def seed_admin(user_repo: UserRepository):
    if not is_mongo_connected():
        logger.info("[seed] Skipping admin seed because MongoDB is not connected.")
        return

    email = settings.DEFAULT_ADMIN_EMAIL
    existing = await user_repo.find_by_email(email)
    if existing:
        return

    hashed = hash_password(settings.DEFAULT_ADMIN_PASSWORD)
    admin_user = UserDocument(
        fullName=settings.DEFAULT_ADMIN_NAME,
        email=email,
        password=hashed,
        role=UserRole.ADMIN,
    )
    await user_repo.create(admin_user)
    logger.info(f"[seed] Default admin account seeded: {email}")
