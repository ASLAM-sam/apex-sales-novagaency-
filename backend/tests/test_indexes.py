import pytest
from app.db.indexes import INDEX_SPECIFICATIONS, initialize_mongodb_indexes


def test_index_specifications_completeness():
    required_collections = {
        "businesses",
        "leads",
        "research",
        "website_audits",
        "outreach",
        "conversations",
        "campaigns",
        "agent_runs",
        "ai_generations",
    }
    assert set(INDEX_SPECIFICATIONS.keys()) == required_collections

    for coll_name, indexes in INDEX_SPECIFICATIONS.items():
        assert len(indexes) > 0, f"Collection {coll_name} has no index specifications"


@pytest.mark.asyncio
async def test_initialize_mongodb_indexes_unconnected():
    # When MongoDB is not connected, initialize_mongodb_indexes should skip gracefully
    result = await initialize_mongodb_indexes()
    assert result["status"] == "skipped"
    assert result["reason"] == "MongoDB not connected"
