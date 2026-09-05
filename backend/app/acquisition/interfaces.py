from abc import ABC, abstractmethod
from typing import List
from app.acquisition.schemas import AcquisitionSearchRequest
from app.discovery.models import DiscoveredCandidate


class BaseLeadSource(ABC):
    """
    Provider-independent abstract base class for lead sources.
    Sources only gather and normalize candidate business details.
    Must NOT contain MongoDB database logic or LLM generation logic.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier key for the lead source."""
        pass

    @abstractmethod
    async def search(self, request: AcquisitionSearchRequest) -> List[DiscoveredCandidate]:
        """
        Executes a search request and returns candidate business models.
        """
        pass
