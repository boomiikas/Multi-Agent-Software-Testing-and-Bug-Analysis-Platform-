from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson.objectid import ObjectId
from ..models.user import UserDocument, ResetTokenDocument, utc_now_iso
from ..database import get_database


def _doc_to_user(doc: dict) -> UserDocument:
    raw_id = doc.pop("_id", None)
    if "id" not in doc and raw_id is not None:
        doc["id"] = str(raw_id)
    return UserDocument(**doc)


def _id_query(user_id: str) -> dict:
    if ObjectId.is_valid(user_id):
        return {"$or": [{"id": user_id}, {"_id": ObjectId(user_id)}]}
    return {"id": user_id}


class UserRepository:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db = db

    def _get_db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_database()

    async def find_all(self) -> List[UserDocument]:
        db = self._get_db()
        cursor = db.users.find({})
        users = []
        async for doc in cursor:
            users.append(_doc_to_user(doc))
        return users

    async def find_by_id(self, user_id: str) -> Optional[UserDocument]:
        db = self._get_db()
        doc = await db.users.find_one(_id_query(user_id))
        if not doc:
            return None
        return _doc_to_user(doc)

    async def find_by_email(self, email: str) -> Optional[UserDocument]:
        db = self._get_db()
        doc = await db.users.find_one({"email": email.lower()})
        if not doc:
            return None
        return _doc_to_user(doc)

    async def create(self, user: UserDocument) -> UserDocument:
        db = self._get_db()
        user_dict = user.model_dump()
        await db.users.insert_one(user_dict)
        return user

    async def update(self, user_id: str, updates: dict) -> Optional[UserDocument]:
        db = self._get_db()
        updates["updatedAt"] = utc_now_iso()
        res = await db.users.find_one_and_update(
            _id_query(user_id),
            {"$set": updates},
            return_document=True,
        )
        if not res:
            return None
        return _doc_to_user(res)

    async def delete(self, user_id: str) -> bool:
        db = self._get_db()
        res = await db.users.delete_one(_id_query(user_id))
        return res.deleted_count > 0


    async def save_reset_token(self, user_id: str, token_hash: str, expires_at: float):
        db = self._get_db()
        # Invalidate old tokens for user
        await db.reset_tokens.delete_many({"userId": user_id})
        await db.reset_tokens.insert_one({
            "userId": user_id,
            "tokenHash": token_hash,
            "expiresAt": expires_at,
        })

    async def find_reset_token(self, token_hash: str) -> Optional[ResetTokenDocument]:
        db = self._get_db()
        doc = await db.reset_tokens.find_one({"tokenHash": token_hash})
        if not doc:
            return None
        doc.pop("_id", None)
        return ResetTokenDocument(**doc)

    async def delete_reset_token(self, token_hash: str):
        db = self._get_db()
        await db.reset_tokens.delete_many({"tokenHash": token_hash})


def get_user_repository() -> UserRepository:
    return UserRepository()
