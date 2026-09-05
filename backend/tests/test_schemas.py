from bson import ObjectId
import pytest
from pydantic import ValidationError

from app.schemas import (
    AgentRun,
    AgentRunStatus,
    AgentType,
    AIGeneration,
    AIGenerationValidation,
    AuditIssue,
    Business,
    BusinessStatus,
    Campaign,
    CampaignStatus,
    Contact,
    Conversation,
    ConversationIntent,
    ConversationStatus,
    Evidence,
    EvidenceType,
    IssueSeverity,
    Lead,
    LeadSource,
    LeadStatus,
    Outreach,
    OutreachChannel,
    OutreachDirection,
    OutreachMessageType,
    OutreachStatus,
    PipelineStage,
    Qualification,
    Research,
    ResearchSource,
    ServiceOpportunity,
    ServiceType,
    SocialProfiles,
    SourceRecord,
    VerificationStatus,
    WebsiteAudit,
)


def test_business_schema_valid():
    biz = Business(
        name="Acme Digital",
        normalized_name="acme digital",
        website="https://acmedigital.com",
        normalized_domain="acmedigital.com",
        phone="+15550199",
        normalized_phone="15550199",
        email="contact@acmedigital.com",
        business_status=BusinessStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED,
        social_profiles=SocialProfiles(instagram="https://instagram.com/acme"),
        source_records=[SourceRecord(source_type="google_maps", source_name="Google")],
    )
    assert biz.name == "Acme Digital"
    assert biz.business_status == BusinessStatus.ACTIVE
    assert biz.verification_status == VerificationStatus.VERIFIED
    assert biz.social_profiles.instagram == "https://instagram.com/acme"
    assert len(biz.source_records) == 1


def test_business_schema_invalid_enum():
    with pytest.raises(ValidationError):
        Business(name="Bad Biz", business_status="NOT_A_STATUS")  # type: ignore


def test_lead_schema_valid_and_scores():
    biz_id = str(ObjectId())
    lead = Lead(
        business_id=biz_id,
        contact=Contact(name="John Doe", email="john@example.com"),
        lead_source=LeadSource.GOOGLE_MAPS,
        lead_status=LeadStatus.QUALIFIED,
        pipeline_stage=PipelineStage.PITCH_READY,
        score=85.0,
        qualification=Qualification(
            is_genuine_business=True,
            website_quality=40.0,
            website_need=90.0,
            qualification_score=85.0,
            qualification_reason="No responsive layout and missing CTA",
        ),
        evidence=[
            Evidence(
                type=EvidenceType.NO_WEBSITE,
                description="Business lacks functional website",
                confidence=95.0,
            )
        ],
    )
    assert str(lead.business_id) == biz_id
    assert lead.score == 85.0
    assert lead.qualification.qualification_score == 85.0
    assert lead.evidence[0].type == EvidenceType.NO_WEBSITE


@pytest.mark.parametrize("invalid_score", [-1.0, 100.5, 150.0])
def test_lead_score_out_of_bounds(invalid_score):
    biz_id = str(ObjectId())
    with pytest.raises(ValidationError):
        Lead(business_id=biz_id, score=invalid_score)

    with pytest.raises(ValidationError):
        Qualification(qualification_score=invalid_score)


@pytest.mark.parametrize("valid_score", [0.0, 50.0, 100.0])
def test_lead_score_boundary_valid(valid_score):
    biz_id = str(ObjectId())
    lead = Lead(business_id=biz_id, score=valid_score)
    assert lead.score == valid_score


def test_lead_invalid_enum():
    biz_id = str(ObjectId())
    with pytest.raises(ValidationError):
        Lead(business_id=biz_id, lead_status="INVALID_LEAD_STATUS")  # type: ignore

    with pytest.raises(ValidationError):
        Lead(business_id=biz_id, pipeline_stage="UNKNOWN_STAGE")  # type: ignore

def test_research_schema():
    biz_id = str(ObjectId())
    lead_id = str(ObjectId())
    research = Research(
        business_id=biz_id,
        lead_id=lead_id,
        business_summary="Local bakery seeking online order solution",
        products_services=["Cakes", "Pastries"],
        research_sources=[ResearchSource(source_type="website", source_url="http://bakery.com")],
        research_confidence=90.0,
    )
    assert str(research.business_id) == biz_id
    assert research.research_confidence == 90.0
    assert len(research.research_sources) == 1


def test_research_invalid_confidence():
    biz_id = str(ObjectId())
    with pytest.raises(ValidationError):
        Research(business_id=biz_id, research_confidence=120.0)


def test_website_audit_schema():
    biz_id = str(ObjectId())
    audit = WebsiteAudit(
        business_id=biz_id,
        website_url="https://example.com",
        domain="example.com",
        website_exists=True,
        performance_score=45.0,
        seo_score=60.0,
        overall_score=52.5,
        issues=[
            AuditIssue(
                category="performance",
                severity=IssueSeverity.HIGH,
                title="Slow page load",
                description="Largest Contentful Paint exceeds 4 seconds",
            )
        ],
    )
    assert audit.overall_score == 52.5
    assert audit.issues[0].severity == IssueSeverity.HIGH


def test_outreach_schema():
    lead_id = str(ObjectId())
    biz_id = str(ObjectId())
    outreach = Outreach(
        lead_id=lead_id,
        business_id=biz_id,
        channel=OutreachChannel.EMAIL,
        direction=OutreachDirection.OUTBOUND,
        message_type=OutreachMessageType.INITIAL_PITCH,
        subject="Modernize your website",
        message="Hi, we noticed your website could use a mobile update...",
        status=OutreachStatus.DRAFT,
    )
    assert outreach.channel == OutreachChannel.EMAIL
    assert outreach.status == OutreachStatus.DRAFT


def test_outreach_invalid_channel():
    lead_id = str(ObjectId())
    biz_id = str(ObjectId())
    with pytest.raises(ValidationError):
        Outreach(
            lead_id=lead_id,
            business_id=biz_id,
            channel="TELEPATHY",  # type: ignore
            message="Hello",
        )


def test_conversation_schema():
    lead_id = str(ObjectId())
    biz_id = str(ObjectId())
    conv = Conversation(
        lead_id=lead_id,
        business_id=biz_id,
        channel=OutreachChannel.WHATSAPP,
        status=ConversationStatus.REPLIED,
        intent=ConversationIntent.INTERESTED,
        message_count=3,
    )
    assert conv.status == ConversationStatus.REPLIED
    assert conv.intent == ConversationIntent.INTERESTED


def test_campaign_schema():
    campaign = Campaign(
        name="Q3 Local Retailers",
        status=CampaignStatus.RUNNING,
        target_service=ServiceType.WEBSITE_REDESIGN,
        total_leads=50,
        contacted_count=20,
    )
    assert campaign.status == CampaignStatus.RUNNING
    assert campaign.target_service == ServiceType.WEBSITE_REDESIGN


def test_agent_run_schema():
    biz_id = str(ObjectId())
    run = AgentRun(
        agent_type=AgentType.LEAD_QUALIFICATION,
        status=AgentRunStatus.COMPLETED,
        business_id=biz_id,
        duration_ms=1250,
        tokens_input=450,
        tokens_output=120,
    )
    assert run.agent_type == AgentType.LEAD_QUALIFICATION
    assert run.status == AgentRunStatus.COMPLETED


def test_ai_generation_schema():
    gen = AIGeneration(
        task_type="pitch_generation",
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        output_text="Dear Store Owner...",
        structured_output={"pitch_angle": "mobile-friendly"},
        validation_status=AIGenerationValidation.VALID,
    )
    assert gen.validation_status == AIGenerationValidation.VALID
    assert gen.model == "anthropic/claude-3.5-sonnet"

