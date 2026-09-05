from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class CampaignRepository(BaseRepository):
    def __init__(self):
        super().__init__("campaigns")

    async def list_campaigns(
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
