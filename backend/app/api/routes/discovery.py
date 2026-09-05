from fastapi import APIRouter, HTTPException, status
from app.discovery.exceptions import InvalidDiscoveryRequestError, UnsupportedDiscoverySourceError
from app.discovery.schemas import DiscoverySearchRequest, DiscoverySearchResponse
from app.discovery.service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["Discovery"])
discovery_service = DiscoveryService()


@router.post("/search", response_model=DiscoverySearchResponse, status_code=status.HTTP_200_OK)
async def search_leads(request: DiscoverySearchRequest) -> DiscoverySearchResponse:
    """
    Search for lead candidates using a specified discovery source.
    Converts valid candidates into normalized Business and Lead records.
    """
    try:
        return await discovery_service.discover(request)
    except UnsupportedDiscoverySourceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except InvalidDiscoveryRequestError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while executing discovery search.",
        )
