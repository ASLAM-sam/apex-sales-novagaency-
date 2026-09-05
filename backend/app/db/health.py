from typing import Any, Dict
from app.db.mongodb import check_mongodb_health
from app.db.sqlite import check_sqlite_health


async def get_database_health() -> Dict[str, Any]:
    """
    Aggregates database health status across MongoDB and SQLite.
    Excludes sensitive connection parameters, passwords, or tokens.
    """
    mongo_health = await check_mongodb_health()
    sqlite_health = await check_sqlite_health()

    return {
        "mongodb": mongo_health,
        "sqlite": sqlite_health,
    }
