from fastapi import APIRouter, Response, status
from app.api.routes import (
    acquisition,
    businesses,
    campaigns,
    conversations,
    dashboard,
    discovery,
    intelligence,
    leads,
    outreach,
    pitch,
    qualification,
    research,
    sales,
    website_audits,
)
from app.db.health import get_database_health

api_router = APIRouter()

# Health & Readiness Check Endpoints
@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Process health check endpoint.
    Indicates whether the API process is alive.
    Independent of external database connectivity.
    """
    return {
        "status": "ok",
        "service": "apex-api",
        "version": "0.1.0",
    }


@api_router.get("/ready", tags=["Health"])
async def readiness_check(response: Response):
    """
    Infrastructure readiness endpoint.
    Verifies connectivity to MongoDB and SQLite databases.
    """
    db_health = await get_database_health()
    mongo_status = db_health.get("mongodb", {}).get("status", "unhealthy")
    sqlite_status = db_health.get("sqlite", {}).get("status", "unhealthy")

    is_ready = (mongo_status == "healthy") and (sqlite_status == "healthy")

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "mongodb": mongo_status,
            "sqlite": sqlite_status,
        }

    return {
        "status": "ready",
        "mongodb": mongo_status,
        "sqlite": sqlite_status,
    }


# API v1 Router Registration
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(businesses.router)
v1_router.include_router(leads.router)
v1_router.include_router(research.router)
v1_router.include_router(website_audits.router)
v1_router.include_router(outreach.router)
v1_router.include_router(conversations.router)
v1_router.include_router(campaigns.router)
v1_router.include_router(discovery.router)
v1_router.include_router(intelligence.router)
v1_router.include_router(qualification.router)
v1_router.include_router(pitch.router)
v1_router.include_router(acquisition.router)
v1_router.include_router(dashboard.router)
v1_router.include_router(sales.router)

api_router.include_router(v1_router)


