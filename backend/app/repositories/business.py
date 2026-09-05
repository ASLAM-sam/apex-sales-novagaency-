from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository):
    def __init__(self):
        super().__init__("businesses")

    async def get_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        coll = self._get_collection()
        return await coll.find_one({"normalized_domain": domain.strip().lower()})

    async def get_by_normalized_name(self, name: str) -> Optional[Dict[str, Any]]:
        coll = self._get_collection()
        return await coll.find_one({"normalized_name": name.strip().lower()})

    async def get_by_normalized_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        coll = self._get_collection()
        return await coll.find_one({"normalized_phone": phone.strip().lower()})

    async def list_businesses(
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
