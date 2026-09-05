import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict
import aiosqlite

from app.core.config import settings
from app.core.logging import logger


class SQLiteManager:
    """
    SQLite Database Manager using aiosqlite.
    Manages local/system state database lifecycle, directory setup, pragmas, and health checks.
    """

    def __init__(self) -> None:
        self.db_path: str = settings.SQLITE_DATABASE_PATH
        self._is_initialized: bool = False

    def _ensure_directory_exists(self) -> None:
        """
        Creates parent directory for SQLite database if it does not exist.
        """
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created SQLite data directory: {directory}")

    async def initialize(self) -> None:
        """
        Initializes SQLite database, applies pragmas, and creates system metadata table.
        """
        logger.info("SQLite initialization started")
        try:
            self._ensure_directory_exists()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON;")
                await db.execute("PRAGMA busy_timeout = 5000;")
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
                await db.commit()
            self._is_initialized = True
            logger.info("SQLite initialized successfully")
        except Exception as exc:
            self._is_initialized = False
            logger.error(f"SQLite connection failed: {exc}")
            raise

    async def close(self) -> None:
        """
        Cleans up SQLite resources on shutdown.
        """
        logger.info("SQLite manager shutdown completed")
        self._is_initialized = False

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """
        Async context manager providing a configured SQLite connection.
        """
        self._ensure_directory_exists()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            yield db

    async def check_health(self) -> Dict[str, Any]:
        """
        Verifies SQLite database access with a simple query.
        """
        try:
            self._ensure_directory_exists()
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT 1;") as cursor:
                    result = await cursor.fetchone()
                    if result and result[0] == 1:
                        return {"status": "healthy"}
            return {"status": "unhealthy", "details": "Query check failed"}
        except Exception as exc:
            return {"status": "unhealthy", "details": str(exc)}


sqlite_manager = SQLiteManager()


async def init_sqlite() -> None:
    await sqlite_manager.initialize()


async def close_sqlite() -> None:
    await sqlite_manager.close()


@asynccontextmanager
async def get_sqlite_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with sqlite_manager.get_connection() as conn:
        yield conn


async def check_sqlite_health() -> Dict[str, Any]:
    return await sqlite_manager.check_health()
