from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException
from loguru import logger
from .config import settings
from .logging_config import sanitize_url

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None
_is_connected: bool = False


async def connect_to_mongo() -> bool:
    global _client, _db, _is_connected
    sanitized = sanitize_url(settings.MONGODB_URL)
    try:
        logger.info(f"Connecting to MongoDB at {sanitized}...")
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
        )
        # Verify connection via admin ping
        await _client.admin.command("ping")
        _db = _client[settings.MONGODB_DB_NAME]
        _is_connected = True
        logger.info(f"MongoDB connected successfully to database: {settings.MONGODB_DB_NAME}")

        # Ensure collections & indexes
        await _ensure_indexes(_db)
        return True
    except Exception as e:
        _is_connected = False
        logger.warning(
            f"MongoDB connection failed to {sanitized} ({type(e).__name__}: {e}). "
            "Server will start in degraded mode (database-dependent endpoints will return 503)."
        )
        return False


async def _ensure_indexes(db: AsyncIOMotorDatabase):
    try:
        # Unique email on users
        await db.users.create_index("email", unique=True)
        # Token hash lookup on reset_tokens
        await db.reset_tokens.create_index("tokenHash")
        await db.reset_tokens.create_index("userId")
        # Projects lookup by owner and status
        await db.projects.create_index("ownerId")
        await db.projects.create_index("createdAt")
        # Test runs lookup by project, status, and startTime
        await db.testruns.create_index("projectId")
        await db.testruns.create_index("startTime")
        await db.testruns.create_index("status")
        logger.info("MongoDB indexes verified.")
    except Exception as e:
        logger.warning(f"Could not initialize MongoDB indexes: {e}")


async def close_mongo_connection():
    global _client, _db, _is_connected
    if _client:
        logger.info("Closing MongoDB connection...")
        _client.close()
        _client = None
        _db = None
        _is_connected = False
        logger.info("MongoDB connection closed.")


def is_mongo_connected() -> bool:
    return _is_connected


def get_database() -> AsyncIOMotorDatabase:
    if not _is_connected or _db is None:
        raise HTTPException(
            status_code=503,
            detail="Database service is unavailable. Please ensure MongoDB is running.",
        )
    return _db
