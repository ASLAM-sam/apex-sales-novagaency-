from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class WebsiteAuditRepository(BaseRepository):
    def __init__(self):
        super().__init__("website_audits")

    async def get_by_business_id(self, business_id: str) -> List[Dict[str, Any]]:
        oid = self.parse_object_id(business_id)
        coll = self._get_collection()
        cursor = coll.find({"business_id": oid}).sort("audited_at", -1)
        return await cursor.to_list(length=100)

    async def get_latest_for_business(self, business_id: str) -> Optional[Dict[str, Any]]:
        oid = self.parse_object_id(business_id)
        coll = self._get_collection()
        return await coll.find_one({"business_id": oid}, sort=[("audited_at", -1)])

    async def get_by_lead_id(self, lead_id: str) -> List[Dict[str, Any]]:
        oid = self.parse_object_id(lead_id)
        coll = self._get_collection()
        cursor = coll.find({"lead_id": oid}).sort("audited_at", -1)
        return await cursor.to_list(length=100)

    async def list_audits(
        self,
        query: Dict[str, Any],
        skip: int,
        limit: int,
        sort_field: str = "audited_at",
        sort_dir: int = -1,
    ) -> Tuple[List[Dict[str, Any]], int]:
        total = await self.count(query)
        items = await self.list_paginated(query, skip, limit, sort_field, sort_dir)
        return items, total
