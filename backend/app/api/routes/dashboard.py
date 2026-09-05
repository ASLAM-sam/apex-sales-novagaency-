import logging
from fastapi import APIRouter, Depends, status
from app.sales.schemas import DashboardSummaryResponse
from app.sales.service import SalesWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Sales Workspace Dashboard"])


def get_sales_workspace_service() -> SalesWorkspaceService:
    return SalesWorkspaceService()


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Sales Workspace Dashboard Summary Metrics",
    description="Returns aggregate database counts for businesses, leads, statuses, qualification scores, and outreach drafts.",
)
async def get_dashboard_summary(
    service: SalesWorkspaceService = Depends(get_sales_workspace_service),
) -> DashboardSummaryResponse:
    return await service.get_dashboard_summary()
