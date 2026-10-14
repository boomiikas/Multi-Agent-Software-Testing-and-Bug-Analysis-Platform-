from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson.objectid import ObjectId
from ..models.project import ProjectDocument, utc_now_iso
from ..database import get_database


def _doc_to_project(doc: dict) -> ProjectDocument:
    raw_id = doc.pop("_id", None)
    if "id" not in doc and raw_id is not None:
        doc["id"] = str(raw_id)
    return ProjectDocument(**doc)


def _id_query(project_id: str) -> dict:
    if ObjectId.is_valid(project_id):
        return {"$or": [{"id": project_id}, {"_id": ObjectId(project_id)}]}
    return {"id": project_id}


class ProjectRepository:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db = db

    def _get_db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_database()

    async def find_all(self) -> List[ProjectDocument]:
        db = self._get_db()
        cursor = db.projects.find({}).sort("createdAt", -1)
        projects = []
        async for doc in cursor:
            projects.append(_doc_to_project(doc))
        return projects

    async def find_by_owner_id(self, owner_id: str) -> List[ProjectDocument]:
        db = self._get_db()
        cursor = db.projects.find({"ownerId": owner_id}).sort("createdAt", -1)
        projects = []
        async for doc in cursor:
            projects.append(_doc_to_project(doc))
        return projects

    async def find_by_id(self, project_id: str) -> Optional[ProjectDocument]:
        db = self._get_db()
        doc = await db.projects.find_one(_id_query(project_id))
        if not doc:
            return None
        return _doc_to_project(doc)

    async def create(self, project: ProjectDocument) -> ProjectDocument:
        db = self._get_db()
        p_dict = project.model_dump()
        await db.projects.insert_one(p_dict)
        return project

    async def update(self, project_id: str, updates: dict) -> Optional[ProjectDocument]:
        db = self._get_db()
        updates["updatedAt"] = utc_now_iso()
        res = await db.projects.find_one_and_update(
            _id_query(project_id),
            {"$set": updates},
            return_document=True,
        )
        if not res:
            return None
        return _doc_to_project(res)

    async def delete(self, project_id: str) -> bool:
        db = self._get_db()
        res = await db.projects.delete_one(_id_query(project_id))
        return res.deleted_count > 0


def get_project_repository() -> ProjectRepository:
    return ProjectRepository()

