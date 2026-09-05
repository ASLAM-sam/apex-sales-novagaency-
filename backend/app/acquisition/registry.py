from typing import Dict, Optional
from app.acquisition.exceptions import UnsupportedAcquisitionSourceError
from app.acquisition.interfaces import BaseLeadSource
from app.acquisition.sources.manual import ManualLeadSource


class SourceRegistry:
    """
    Registry for managing available lead acquisition sources.
    """

    def __init__(self) -> None:
        self._sources: Dict[str, BaseLeadSource] = {}

    def register(self, source: BaseLeadSource) -> None:
        key = source.source_name.lower().strip()
        self._sources[key] = source

    def get(self, source_name: str) -> BaseLeadSource:
        key = source_name.lower().strip()
        if key not in self._sources:
            raise UnsupportedAcquisitionSourceError(
                f"Lead acquisition source '{source_name}' is not registered."
            )
        return self._sources[key]


def get_default_registry() -> SourceRegistry:
    registry = SourceRegistry()
    registry.register(ManualLeadSource())
    return registry
