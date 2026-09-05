from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.discovery.models import DiscoverySummaryData


class DiscoverySearchRequest(BaseModel):
    """
    Input request schema for starting a discovery run.
    """

    query: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    max_results: int = Field(default=25, ge=1, le=100)
    source: str = Field(default="manual")
    manual_candidates: Optional[List[Any]] = None


class DiscoverySearchResponse(BaseModel):
    """
    Standard JSON API response wrapper for discovery search endpoint.
    """

    data: DiscoverySummaryData
