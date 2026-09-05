"""
Pydantic Schemas Package for Apex Sales AI Domain Models.
"""

from app.schemas.agent_run import AgentRun
from app.schemas.ai_generation import AIGeneration
from app.schemas.business import Business, SocialProfiles, SourceRecord
from app.schemas.campaign import Campaign
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now, validate_score_range
from app.schemas.conversation import Conversation
from app.schemas.enums import (
    AgentRunStatus,
    AgentType,
    AIGenerationValidation,
    BusinessStatus,
    CampaignStatus,
    ConversationIntent,
    ConversationStatus,
    EvidenceType,
    IssueSeverity,
    LeadSource,
    LeadStatus,
    OutreachChannel,
    OutreachDirection,
    OutreachMessageType,
    OutreachStatus,
    PipelineStage,
    ServiceType,
    VerificationStatus,
)
from app.schemas.lead import Contact, Evidence, Lead, Qualification, ServiceOpportunity, SourceReference
from app.schemas.outreach import Outreach
from app.schemas.research import Research, ResearchSource
from app.schemas.website_audit import AuditIssue, WebsiteAudit

__all__ = [
    "MongoBaseModel",
    "PyObjectId",
    "utc_now",
    "validate_score_range",
    # Enums
    "BusinessStatus",
    "VerificationStatus",
    "LeadSource",
    "LeadStatus",
    "PipelineStage",
    "ServiceType",
    "EvidenceType",
    "IssueSeverity",
    "OutreachChannel",
    "OutreachDirection",
    "OutreachMessageType",
    "OutreachStatus",
    "ConversationStatus",
    "ConversationIntent",
    "CampaignStatus",
    "AgentType",
    "AgentRunStatus",
    "AIGenerationValidation",
    # Schemas
    "Business",
    "SocialProfiles",
    "SourceRecord",
    "Lead",
    "Contact",
    "SourceReference",
    "Qualification",
    "ServiceOpportunity",
    "Evidence",
    "Research",
    "ResearchSource",
    "WebsiteAudit",
    "AuditIssue",
    "Outreach",
    "Conversation",
    "Campaign",
    "AgentRun",
    "AIGeneration",
]

