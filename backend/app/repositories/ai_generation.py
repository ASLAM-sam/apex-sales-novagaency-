from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class AIGenerationRepository(BaseRepository):
    def __init__(self):
        super().__init__("ai_generations")

    async def find_by_agent_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        oid = self.parse_object_id(run_id)
        coll = self._get_collection()
        cursor = coll.find({"agent_run_id": oid}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def find_by_task_type(self, task_type: str) -> List[Dict[str, Any]]:
        coll = self._get_collection()
        cursor = coll.find({"task_type": task_type}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def list_generations(
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
