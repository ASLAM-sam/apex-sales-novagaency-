from typing import Any, Dict, List
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.core.exceptions import DatabaseError
from app.core.logging import logger
from app.db.mongodb import mongodb_manager


INDEX_SPECIFICATIONS: Dict[str, List[IndexModel]] = {
    "businesses": [
        IndexModel([("normalized_domain", ASCENDING)], name="idx_businesses_domain"),
        IndexModel([("normalized_name", ASCENDING)], name="idx_businesses_name"),
        IndexModel([("normalized_phone", ASCENDING)], name="idx_businesses_phone"),
        IndexModel([("verification_status", ASCENDING)], name="idx_businesses_verification"),
        IndexModel([("created_at", DESCENDING)], name="idx_businesses_created_at"),
    ],
    "leads": [
        IndexModel([("business_id", ASCENDING)], name="idx_leads_business_id"),
        IndexModel([("lead_status", ASCENDING)], name="idx_leads_status"),
        IndexModel([("pipeline_stage", ASCENDING)], name="idx_leads_pipeline_stage"),
        IndexModel([("lead_source", ASCENDING)], name="idx_leads_source"),
        IndexModel([("qualification.qualification_score", DESCENDING)], name="idx_leads_qual_score"),
        IndexModel([("next_follow_up_at", ASCENDING)], name="idx_leads_next_follow_up"),
        IndexModel([("created_at", DESCENDING)], name="idx_leads_created_at"),
    ],
    "research": [
        IndexModel([("business_id", ASCENDING)], name="idx_research_business_id"),
        IndexModel([("lead_id", ASCENDING)], name="idx_research_lead_id"),
        IndexModel([("created_at", DESCENDING)], name="idx_research_created_at"),
    ],
    "website_audits": [
        IndexModel([("business_id", ASCENDING)], name="idx_audits_business_id"),
        IndexModel([("lead_id", ASCENDING)], name="idx_audits_lead_id"),
        IndexModel([("audited_at", DESCENDING)], name="idx_audits_audited_at"),
        IndexModel([("overall_score", DESCENDING)], name="idx_audits_overall_score"),
    ],
    "outreach": [
        IndexModel([("lead_id", ASCENDING)], name="idx_outreach_lead_id"),
        IndexModel([("business_id", ASCENDING)], name="idx_outreach_business_id"),
        IndexModel([("channel", ASCENDING)], name="idx_outreach_channel"),
        IndexModel([("status", ASCENDING)], name="idx_outreach_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_outreach_created_at"),
    ],
    "conversations": [
        IndexModel([("lead_id", ASCENDING)], name="idx_conversations_lead_id"),
        IndexModel([("business_id", ASCENDING)], name="idx_conversations_business_id"),
        IndexModel([("status", ASCENDING)], name="idx_conversations_status"),
        IndexModel([("last_message_at", DESCENDING)], name="idx_conversations_last_msg"),
        IndexModel([("next_follow_up_at", ASCENDING)], name="idx_conversations_next_follow_up"),
    ],
    "campaigns": [
        IndexModel([("status", ASCENDING)], name="idx_campaigns_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_campaigns_created_at"),
    ],
    "agent_runs": [
        IndexModel([("agent_type", ASCENDING)], name="idx_agent_runs_type"),
        IndexModel([("status", ASCENDING)], name="idx_agent_runs_status"),
        IndexModel([("lead_id", ASCENDING)], name="idx_agent_runs_lead_id"),
        IndexModel([("business_id", ASCENDING)], name="idx_agent_runs_business_id"),
        IndexModel([("created_at", DESCENDING)], name="idx_agent_runs_created_at"),
    ],
    "ai_generations": [
        IndexModel([("agent_run_id", ASCENDING)], name="idx_ai_gen_agent_run_id"),
        IndexModel([("task_type", ASCENDING)], name="idx_ai_gen_task_type"),
        IndexModel([("model", ASCENDING)], name="idx_ai_gen_model"),
        IndexModel([("created_at", DESCENDING)], name="idx_ai_gen_created_at"),
    ],
}


async def initialize_mongodb_indexes() -> Dict[str, Any]:
    """
    Idempotently creates MongoDB collection indexes.
    Skips gracefully if MongoDB is not connected or configured.
    """
    try:
        db = mongodb_manager.get_database()
    except DatabaseError:
        logger.warning("MongoDB not connected. Skipping index initialization.")
        return {"status": "skipped", "reason": "MongoDB not connected"}

    results: Dict[str, List[str]] = {}
    logger.info("Initializing MongoDB indexes...")

    for collection_name, indexes in INDEX_SPECIFICATIONS.items():
        try:
            collection = db[collection_name]
            created = await collection.create_indexes(indexes)
            results[collection_name] = created
            logger.info(f"Created indexes for collection '{collection_name}': {created}")
        except Exception as exc:
            logger.error(f"Failed to create indexes for collection '{collection_name}': {exc}")
            results[collection_name] = [f"Error: {exc}"]

    return {"status": "success", "collections": results}
