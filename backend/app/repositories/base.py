from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError
from app.core.exceptions import DatabaseError, InvalidObjectIdError
from app.db.mongodb import mongodb_manager


class BaseRepository:
    """Base repository providing generic MongoDB persistence operations."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def _get_collection(self):
        try:
            db = mongodb_manager.get_database()
            return db[self.collection_name]
        except Exception as exc:
            raise DatabaseError(f"Database connection unavailable: {exc}")

    @staticmethod
    def parse_object_id(id_str: Any) -> ObjectId:
        """Validates and converts string or ObjectId to ObjectId."""
        if isinstance(id_str, ObjectId):
            return id_str
        if isinstance(id_str, str) and ObjectId.is_valid(id_str):
            return ObjectId(id_str)
        raise InvalidObjectIdError(f"Invalid ObjectId format: '{id_str}'")

    async def create(self, document: Dict[str, Any]) -> Dict[str, Any]:
        coll = self._get_collection()
        try:
            res = await coll.insert_one(document)
            document["_id"] = res.inserted_id
            return document
        except PyMongoError as exc:
            raise DatabaseError(f"Error inserting document: {exc}")

    async def get_by_id(self, id_str: str) -> Optional[Dict[str, Any]]:
        oid = self.parse_object_id(id_str)
        coll = self._get_collection()
        try:
            return await coll.find_one({"_id": oid})
        except PyMongoError as exc:
            raise DatabaseError(f"Error querying document by ID: {exc}")

    async def update_by_id(self, id_str: str, update_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = self.parse_object_id(id_str)
        coll = self._get_collection()
        try:
            res = await coll.find_one_and_update(
                {"_id": oid},
                {"$set": update_dict},
                return_document=True,
            )
            return res
        except PyMongoError as exc:
            raise DatabaseError(f"Error updating document: {exc}")

    async def delete_by_id(self, id_str: str) -> bool:
        oid = self.parse_object_id(id_str)
        coll = self._get_collection()
        try:
            res = await coll.delete_one({"_id": oid})
            return res.deleted_count > 0
        except PyMongoError as exc:
            raise DatabaseError(f"Error deleting document: {exc}")

    async def count(self, query: Dict[str, Any]) -> int:
        coll = self._get_collection()
        try:
            return await coll.count_documents(query)
        except PyMongoError as exc:
            raise DatabaseError(f"Error counting documents: {exc}")

    async def list_paginated(
        self,
        query: Dict[str, Any],
        skip: int,
        limit: int,
        sort_field: str = "created_at",
        sort_dir: int = -1,
    ) -> List[Dict[str, Any]]:
        coll = self._get_collection()
        try:
            cursor = coll.find(query).sort(sort_field, sort_dir).skip(skip).limit(limit)
            return await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise DatabaseError(f"Error listing documents: {exc}")
