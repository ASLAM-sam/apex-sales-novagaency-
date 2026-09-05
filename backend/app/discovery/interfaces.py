from abc import ABC, abstractmethod
from typing import List
from app.discovery.models import DiscoveredCandidate
from app.discovery.schemas import DiscoverySearchRequest


class BaseDiscoverySource(ABC):
    """
    Abstract base class / interface for all discovery source adapters.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Returns the unique name identifier of the discovery source."""
        pass

    @abstractmethod
    async def search(self, request: DiscoverySearchRequest) -> List[DiscoveredCandidate]:
        """
        Executes search against the discovery source and returns candidate objects.
        """
        pass
