from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.db import close_mongodb, close_sqlite, connect_mongodb, init_sqlite, initialize_mongodb_indexes

setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle hooks
    logger.info("Initializing database connections...")
    await init_sqlite()
    await connect_mongodb()
    await initialize_mongodb_indexes()
    yield
    # Shutdown lifecycle hooks
    logger.info("Database shutdown started")
    await close_mongodb()
    await close_sqlite()
    logger.info("Database shutdown completed")


app = FastAPI(
    title="Apex Sales AI API",
    description="Backend API for the Apex AI lead generation and sales automation platform.",
    version="0.1.0",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Environment-aware CORS configuration
origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central API router
app.include_router(api_router)


