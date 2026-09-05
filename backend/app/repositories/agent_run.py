from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class AgentRunRepository(BaseRepository):
    def __init__(self):
        super().__init__("agent_runs")

    async def find_by_lead_id(self, lead_id: str) -> List[Dict[str, Any]]:
        oid = self.parse_object_id(lead_id)
        coll = self._get_collection()
        cursor = coll.find({"lead_id": oid}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def find_by_business_id(self, business_id: str) -> List[Dict[str, Any]]:
        oid = self.parse_object_id(business_id)
        coll = self._get_collection()
        cursor = coll.find({"business_id": oid}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def find_by_agent_type(self, agent_type: str) -> List[Dict[str, Any]]:
        coll = self._get_collection()
        cursor = coll.find({"agent_type": agent_type}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def find_failed_runs(self) -> List[Dict[str, Any]]:
        coll = self._get_collection()
        cursor = coll.find({"status": "FAILED"}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def list_runs(
        self,
        query: Dict[str, Any],
        skip: int,
        limit: int,
        sort_field: str = "created_at",
        sort_dir: int = -1,
    ) -> Tuple[List[Dict[str, Any]], int]:
        total = await self.count(query)
        items = await self.list_paginated(query, skip, limit, sort_field, sort_dir)
        return items, total
