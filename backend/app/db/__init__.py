"""
Database Package for Apex Sales AI.
Primary application database: MongoDB
Lightweight local/system operational state: SQLite
"""

from app.db.health import get_database_health
from app.db.indexes import INDEX_SPECIFICATIONS, initialize_mongodb_indexes
from app.db.mongodb import (
    check_mongodb_health,
    close_mongodb,
    connect_mongodb,
    get_database,
    get_mongodb_client,
)
from app.db.sqlite import (
    check_sqlite_health,
    close_sqlite,
    get_sqlite_connection,
    init_sqlite,
)

__all__ = [
    "connect_mongodb",
    "close_mongodb",
    "get_mongodb_client",
    "get_database",
    "check_mongodb_health",
    "init_sqlite",
    "close_sqlite",
    "get_sqlite_connection",
    "check_sqlite_health",
    "get_database_health",
    "initialize_mongodb_indexes",
    "INDEX_SPECIFICATIONS",
]


