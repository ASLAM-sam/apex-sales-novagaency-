import re
from typing import Any, Dict, Optional
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.core.logging import logger


class MongoDBManager:
    """
    MongoDB Database Manager using AsyncMongoClient.
    Manages connection lifecycle, database access, and health checks.
    """

    def __init__(self) -> None:
        self.client: Optional[AsyncMongoClient] = None
        self._is_connected: bool = False

    @staticmethod
    def sanitize_connection_string(uri: str) -> str:
        """
        Removes credentials from connection string for safe logging.
        """
        if not uri:
            return ""
        return re.sub(r"://([^:]+):([^@]+)@", "://***:***@", uri)

    async def connect(self) -> None:
        """
        Initializes MongoDB connection and verifies connectivity via ping.
        Does not raise exceptions on connection failure to allow graceful degradation.
        """
        if self.client is not None and self._is_connected:
            return

        uri = settings.MONGODB_URI.strip()
        if not uri or uri.startswith("YOUR_MONGODB"):
            logger.warning("MongoDB URI not configured. Primary application database running in unconfigured state.")
            self._is_connected = False
            return

        logger.info("MongoDB initialization started")
        try:
            timeout_ms = settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS
            self.client = AsyncMongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
            # Execute ping command to verify server reachability
            await self.client.admin.command("ping")
            self._is_connected = True
            logger.info("MongoDB connected successfully")
        except Exception as exc:
            self._is_connected = False
            safe_msg = self.sanitize_connection_string(str(exc))
            logger.error(f"MongoDB connection failed: {safe_msg}")

    async def close(self) -> None:
        """
        Closes MongoDB client connection cleanly.
        """
        if self.client is not None:
            logger.info("Closing MongoDB connection")
            self.client.close()
            self.client = None
            self._is_connected = False

    def get_client(self) -> Optional[AsyncMongoClient]:
        """
        Returns active MongoDB client instance.
        """
        return self.client

    def get_database(self) -> Any:
        """
        Returns configured MongoDB database instance.
        Raises DatabaseError if client is not connected.
        """
        if self.client is None or not self._is_connected:
            raise DatabaseError("MongoDB client is not connected or configured.")
        return self.client[settings.MONGODB_DATABASE]

    async def check_health(self) -> Dict[str, Any]:
        """
        Performs a lightweight ping check to verify database health.
        Returns health status without exposing credentials.
        """
        uri = settings.MONGODB_URI.strip()
        if not uri or uri.startswith("YOUR_MONGODB"):
            return {
                "status": "unhealthy",
                "details": "MongoDB URI not configured",
            }

        if self.client is None:
            return {
                "status": "unhealthy",
                "details": "MongoDB client not initialized",
            }

        try:
            await self.client.admin.command("ping")
            return {"status": "healthy"}
        except PyMongoError as pme:
            safe_detail = self.sanitize_connection_string(str(pme))
            return {
                "status": "unhealthy",
                "details": safe_detail,
            }
        except Exception as exc:
            safe_detail = self.sanitize_connection_string(str(exc))
            return {
                "status": "unhealthy",
                "details": safe_detail,
            }


mongodb_manager = MongoDBManager()


async def connect_mongodb() -> None:
    await mongodb_manager.connect()


async def close_mongodb() -> None:
    await mongodb_manager.close()


def get_mongodb_client() -> Optional[AsyncMongoClient]:
    return mongodb_manager.get_client()


def get_database() -> Any:
    return mongodb_manager.get_database()


async def check_mongodb_health() -> Dict[str, Any]:
    return await mongodb_manager.check_health()
