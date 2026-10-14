from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson.objectid import ObjectId
from ..models.test_run import TestRunDocument
from ..database import get_database


def _doc_to_run(doc: dict) -> TestRunDocument:
    raw_id = doc.pop("_id", None)
    if "id" not in doc and raw_id is not None:
        doc["id"] = str(raw_id)
    return TestRunDocument(**doc)


def _id_query(run_id: str) -> dict:
    if ObjectId.is_valid(run_id):
        return {"$or": [{"id": run_id}, {"_id": ObjectId(run_id)}]}
    return {"id": run_id}


class TestRunRepository:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db = db

    def _get_db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_database()

    async def find_all(self, limit: int = 50) -> List[TestRunDocument]:
        db = self._get_db()
        cursor = db.testruns.find({}).sort("startTime", -1).limit(limit)
        runs = []
        async for doc in cursor:
            runs.append(_doc_to_run(doc))
        return runs

    async def find_by_id(self, run_id: str) -> Optional[TestRunDocument]:
        db = self._get_db()
        doc = await db.testruns.find_one(_id_query(run_id))
        if not doc:
            return None
        return _doc_to_run(doc)

    async def find_by_project_id(self, project_id: str, limit: int = 50) -> List[TestRunDocument]:
        db = self._get_db()
        cursor = db.testruns.find({"projectId": project_id}).sort("startTime", -1).limit(limit)
        runs = []
        async for doc in cursor:
            runs.append(_doc_to_run(doc))
        return runs

    async def find_by_project_ids(self, project_ids: List[str], limit: int = 50) -> List[TestRunDocument]:
        db = self._get_db()
        cursor = db.testruns.find({"projectId": {"$in": project_ids}}).sort("startTime", -1).limit(limit)
        runs = []
        async for doc in cursor:
            runs.append(_doc_to_run(doc))
        return runs

    async def find_by_statuses(self, statuses: List[str]) -> List[TestRunDocument]:
        db = self._get_db()
        cursor = db.testruns.find({"status": {"$in": statuses}})
        runs = []
        async for doc in cursor:
            runs.append(_doc_to_run(doc))
        return runs

    async def create(self, run: TestRunDocument) -> TestRunDocument:
        db = self._get_db()
        r_dict = run.model_dump()
        await db.testruns.insert_one(r_dict)
        return run

    async def update(self, run_id: str, updates: dict) -> Optional[TestRunDocument]:
        db = self._get_db()
        res = await db.testruns.find_one_and_update(
            _id_query(run_id),
            {"$set": updates},
            return_document=True,
        )
        if not res:
            return None
        return _doc_to_run(res)

    async def delete(self, run_id: str) -> bool:
        db = self._get_db()
        res = await db.testruns.delete_one(_id_query(run_id))
        return res.deleted_count > 0

    async def delete_by_project_id(self, project_id: str) -> int:
        db = self._get_db()
        res = await db.testruns.delete_many({"projectId": project_id})
        return res.deleted_count


def get_test_run_repository() -> TestRunRepository:
    return TestRunRepository()

