import os
import tempfile
import pytest
import aiosqlite
from app.db.sqlite import SQLiteManager, check_sqlite_health, get_sqlite_connection


@pytest.mark.anyio
async def test_sqlite_manager_initialization_and_query():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, "test_sub_dir", "test_apex.sqlite3")
        manager = SQLiteManager()
        manager.db_path = test_db_path

        # Test initialization creates directory and system_metadata table
        await manager.initialize()
        assert os.path.exists(test_db_path)

        # Test health check
        health = await manager.check_health()
        assert health["status"] == "healthy"

        # Test connection & table write/read
        async with manager.get_connection() as db:
            await db.execute(
                "INSERT INTO system_metadata (key, value) VALUES (?, ?);",
                ("version", "0.1.0"),
            )
            await db.commit()

            async with db.execute("SELECT value FROM system_metadata WHERE key = ?;", ("version",)) as cursor:
                row = await cursor.fetchone()
                assert row is not None
                assert row[0] == "0.1.0"

        await manager.close()
