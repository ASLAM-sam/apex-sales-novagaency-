import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from app.core.exceptions import NotFoundError, ValidationError
from app.intelligence.service import LeadIntelligenceService
from app.pitch.schemas import PitchGenerationRequest
from app.pitch.service import PitchGenerationService
from app.qualification.service import LeadQualificationService
from app.repositories.business import BusinessRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.lead import LeadRepository
from app.repositories.outreach import OutreachRepository
from app.repositories.research import ResearchRepository
from app.repositories.website_audit import WebsiteAuditRepository
from app.sales.schemas import (
    ContactActionData,
    DashboardSummaryResponse,
    LeadTimelineResponse,
    ReadinessFlags,
    SalesActionRequest,
    SalesActionResponse,
    SalesLeadDetailResponse,
    SalesLeadListResponse,
    SalesLeadSummary,
    TimelineEvent,
)
from app.sales.utils import prepare_email_action_data, prepare_whatsapp_url
from app.schemas.api import PaginationMetadata
from app.schemas.business import Business
from app.schemas.enums import LeadStatus, OutreachChannel, OutreachStatus
from app.schemas.lead import Lead
from app.schemas.outreach import Outreach

logger = logging.getLogger(__name__)


class SalesWorkspaceService:
    """
    Sales Workspace Service orchestrator.
    Provides sales dashboard metrics, filtered lead listings, unified lead detail read-models,
    timeline assembly, action readiness inspection, and explicit workflow actions.
    """

    def __init__(
        self,
        business_repo: Optional[BusinessRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
        research_repo: Optional[ResearchRepository] = None,
        audit_repo: Optional[WebsiteAuditRepository] = None,
        outreach_repo: Optional[OutreachRepository] = None,
        conversation_repo: Optional[ConversationRepository] = None,
    ) -> None:
        self.business_repo = business_repo or BusinessRepository()
        self.lead_repo = lead_repo or LeadRepository()
        self.research_repo = research_repo or ResearchRepository()
        self.audit_repo = audit_repo or WebsiteAuditRepository()
        self.outreach_repo = outreach_repo or OutreachRepository()
        self.conversation_repo = conversation_repo or ConversationRepository()

    async def get_dashboard_summary(self) -> DashboardSummaryResponse:
        total_businesses = await self.business_repo.count({})
        total_leads = await self.lead_repo.count({})

        new_leads = await self.lead_repo.count({"lead_status": "NEW"})
        qualified_leads = await self.lead_repo.count({"lead_status": "QUALIFIED"})
        high_opportunity_leads = await self.lead_repo.count({
            "$or": [
                {"qualification.qualification_score": {"$gte": 70}},
                {"score": {"$gte": 70}},
            ]
        })

        contacted_leads = await self.lead_repo.count({"lead_status": {"$in": ["CONTACTED", "PITCH_SENT"]}})
        replied_leads = await self.lead_repo.count({"lead_status": "REPLIED"})
        interested_leads = await self.lead_repo.count({"lead_status": "INTERESTED"})
        follow_up_leads = await self.lead_repo.count({"lead_status": "FOLLOW_UP"})
        converted_leads = await self.lead_repo.count({"lead_status": {"$in": ["CONVERTED", "WON"]}})
        lost_leads = await self.lead_repo.count({"lead_status": {"$in": ["LOST", "DO_NOT_CONTACT", "INVALID"]}})
        draft_outreach = await self.outreach_repo.count({"status": "DRAFT"})

        return DashboardSummaryResponse(
            total_businesses=total_businesses,
            total_leads=total_leads,
            new_leads=new_leads,
            qualified_leads=qualified_leads,
            high_opportunity_leads=high_opportunity_leads,
            contacted_leads=contacted_leads,
            replied_leads=replied_leads,
            interested_leads=interested_leads,
            follow_up_leads=follow_up_leads,
            converted_leads=converted_leads,
            lost_leads=lost_leads,
            draft_outreach_count=draft_outreach,
        )
    async def list_sales_leads(
        self,
        page: int = 1,
        page_size: int = 25,
        lead_status: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        service_type: Optional[str] = None,
        city: Optional[str] = None,
        category: Optional[str] = None,
        lead_source: Optional[str] = None,
        verification_status: Optional[str] = None,
        has_website: Optional[bool] = None,
        has_audit: Optional[bool] = None,
        has_pitch: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> SalesLeadListResponse:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        skip = (page - 1) * page_size

        query: Dict[str, Any] = {}

        if lead_status:
            query["lead_status"] = lead_status.strip().upper()
        if pipeline_stage:
            query["pipeline_stage"] = pipeline_stage.strip().upper()
        if lead_source:
            query["lead_source"] = lead_source.strip().upper()

        if min_score is not None or max_score is not None:
            score_query: Dict[str, Any] = {}
            if min_score is not None:
                score_query["$gte"] = min_score
            if max_score is not None:
                score_query["$lte"] = max_score
            query["$or"] = [
                {"qualification.qualification_score": score_query},
                {"score": score_query},
            ]

        if service_type:
            st = service_type.strip().upper()
            query["$or"] = [
                {"service_opportunity.primary_service": st},
                {"qualification.recommended_services": st},
            ]

        # Allowed sort fields
        sort_map = {
            "created_at": "created_at",
            "updated_at": "updated_at",
            "score": "qualification.qualification_score",
            "lead_status": "lead_status",
        }
        clean_sort = sort_map.get(sort_by.lower().strip(), "created_at")
        sort_dir = 1 if sort_order.lower().strip() in ("asc", "1") else -1

        leads_docs, total = await self.lead_repo.list_leads(
            query=query, skip=skip, limit=page_size, sort_field=clean_sort, sort_dir=sort_dir
        )

        summaries: List[SalesLeadSummary] = []

        for ldoc in leads_docs:
            biz_id_str = str(ldoc.get("business_id", ""))
            biz_doc = await self.business_repo.get_by_id(biz_id_str) if biz_id_str else None
            biz_doc = biz_doc or {}

            biz_city = biz_doc.get("city")
            biz_category = biz_doc.get("category")
            biz_ver = biz_doc.get("verification_status")
            biz_website = biz_doc.get("website")

            # Post-filtering for business-level fields if requested
            if city and (not biz_city or city.lower() not in biz_city.lower()):
                continue
            if category and (not biz_category or category.lower() not in biz_category.lower()):
                continue
            if verification_status and biz_ver != verification_status.strip().upper():
                continue
            if has_website is not None and bool(biz_website) != has_website:
                continue

            lead_id_str = str(ldoc["_id"])
            audit_count = await self.audit_repo.count({"business_id": self.audit_repo.parse_object_id(biz_id_str)}) if biz_id_str else 0
            pitch_count = await self.outreach_repo.count({"lead_id": self.outreach_repo.parse_object_id(lead_id_str)})

            if has_audit is not None and (audit_count > 0) != has_audit:
                continue
            if has_pitch is not None and (pitch_count > 0) != has_pitch:
                continue

            qual = ldoc.get("qualification", {})
            contact = ldoc.get("contact", {})

            summary = SalesLeadSummary(
                lead_id=lead_id_str,
                business_id=biz_id_str,
                business_name=biz_doc.get("name", "Unknown Business"),
                website=biz_website,
                phone=contact.get("phone") or biz_doc.get("phone"),
                email=contact.get("email") or biz_doc.get("email"),
                city=biz_city,
                category=biz_category,
                lead_status=str(ldoc.get("lead_status", "NEW")),
                pipeline_stage=str(ldoc.get("pipeline_stage", "NEW")),
                qualification_score=qual.get("qualification_score") or ldoc.get("score"),
                qualification_status=qual.get("qualification_status"),
                primary_service=ldoc.get("service_opportunity", {}).get("primary_service"),
                verification_status=biz_ver,
                has_website=bool(biz_website),
                has_audit=audit_count > 0,
                has_pitch=pitch_count > 0,
                created_at=ldoc.get("created_at"),
                next_follow_up_at=ldoc.get("next_follow_up_at"),
            )
            summaries.append(summary)

        pages = (total + page_size - 1) // page_size if total > 0 else 1
        meta = PaginationMetadata(page=page, page_size=page_size, total=total, pages=pages)
        return SalesLeadListResponse(leads=summaries, pagination=meta)

    async def get_lead_detail(self, lead_id: str) -> SalesLeadDetailResponse:
        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")
        lead_obj = Lead(**lead_doc)

        biz_id_str = str(lead_obj.business_id)
        biz_doc = await self.business_repo.get_by_id(biz_id_str)
        if not biz_doc:
            raise NotFoundError(f"Associated business with ID '{biz_id_str}' not found.")
        biz_obj = Business(**biz_doc)

        # Latest research
        research_coll = self.research_repo._get_collection()
        r_cursor = research_coll.find({"business_id": self.research_repo.parse_object_id(biz_id_str)}).sort("created_at", -1).limit(1)
        r_docs = await r_cursor.to_list(length=1)
        latest_research = r_docs[0] if r_docs else None
        if latest_research and "_id" in latest_research:
            latest_research["id"] = str(latest_research.pop("_id"))

        # Latest audit
        audit_coll = self.audit_repo._get_collection()
        a_cursor = audit_coll.find({"business_id": self.audit_repo.parse_object_id(biz_id_str)}).sort("created_at", -1).limit(1)
        a_docs = await a_cursor.to_list(length=1)
        latest_audit = a_docs[0] if a_docs else None
        if latest_audit and "_id" in latest_audit:
            latest_audit["id"] = str(latest_audit.pop("_id"))

        # Outreach history
        outreach_coll = self.outreach_repo._get_collection()
        o_cursor = outreach_coll.find({"lead_id": self.outreach_repo.parse_object_id(lead_id)}).sort("created_at", -1)
        o_docs = await o_cursor.to_list(length=50)
        all_outreach = [Outreach(**d) for d in o_docs]
        latest_outreach = all_outreach[0] if all_outreach else None

        # Conversation metadata
        conv_coll = self.conversation_repo._get_collection()
        c_cursor = conv_coll.find({"lead_id": self.conversation_repo.parse_object_id(lead_id)}).sort("created_at", -1).limit(1)
        c_docs = await c_cursor.to_list(length=1)
        conversation_meta = c_docs[0] if c_docs else None
        if conversation_meta and "_id" in conversation_meta:
            conversation_meta["id"] = str(conversation_meta.pop("_id"))

        # Readiness Flags
        status_str = str(lead_obj.lead_status.value if hasattr(lead_obj.lead_status, "value") else lead_obj.lead_status)
        is_dnc = status_str in ("DO_NOT_CONTACT", "INVALID")
        has_web = bool(biz_obj.website)
        has_ph = bool(lead_obj.contact.phone or biz_obj.phone)
        has_em = bool(lead_obj.contact.email or biz_obj.email)
        has_draft_outreach = any(o.status == OutreachStatus.DRAFT for o in all_outreach)

        readiness = ReadinessFlags(
            can_verify=not is_dnc,
            can_research=not is_dnc,
            can_audit=not is_dnc and has_web,
            can_qualify=not is_dnc,
            can_generate_pitch=not is_dnc,
            has_email=has_em,
            has_phone=has_ph,
            has_website=has_web,
            has_draft=has_draft_outreach,
            is_do_not_contact=is_dnc,
        )

        score_val = lead_obj.qualification.qualification_score if lead_obj.qualification else lead_obj.score
        if is_dnc:
            next_action = "NONE"
        elif status_str == "NEW":
            next_action = "RUN_INTELLIGENCE"
        elif score_val is None:
            next_action = "QUALIFY"
        elif not has_draft_outreach and (score_val or 0) >= 30:
            next_action = "GENERATE_PITCH"
        elif has_draft_outreach:
            next_action = "REVIEW_PITCH"
        else:
            next_action = "CONTACT"

        target_phone = lead_obj.contact.phone or biz_obj.phone
        target_email = lead_obj.contact.email or biz_obj.email
        latest_draft = next((o for o in all_outreach if o.status == OutreachStatus.DRAFT), latest_outreach)

        wa_url = prepare_whatsapp_url(target_phone, latest_draft.message if latest_draft else None)
        email_data = prepare_email_action_data(lead_obj, latest_draft)

        contact_action = ContactActionData(
            phone=target_phone,
            email=target_email,
            website=biz_obj.website,
            whatsapp_available=bool(wa_url),
            whatsapp_url=wa_url,
            email_available=bool(target_email and latest_draft),
            email_draft=email_data,
            latest_pitch=latest_draft.model_dump(mode="json") if latest_draft else None,
            pitch_channel=str(latest_draft.channel.value if hasattr(latest_draft.channel, "value") else latest_draft.channel) if latest_draft else None,
            pitch_status=str(latest_draft.status.value if hasattr(latest_draft.status, "value") else latest_draft.status) if latest_draft else None,
        )

        pipeline_state = {
            "lead_status": status_str,
            "pipeline_stage": str(lead_obj.pipeline_stage.value if hasattr(lead_obj.pipeline_stage, "value") else lead_obj.pipeline_stage),
            "qualification_score": score_val,
            "verification_status": str(biz_obj.verification_status.value if hasattr(biz_obj.verification_status, "value") else biz_obj.verification_status),
        }

    async def prepare_lead(self, lead_id: str) -> Dict[str, Any]:
        detail = await self.get_lead_detail(lead_id)
        return {
            "lead_id": lead_id,
            "readiness_flags": detail.readiness_flags.model_dump(),
            "next_recommended_action": detail.next_recommended_action,
        }

    async def get_lead_timeline(self, lead_id: str) -> LeadTimelineResponse:
        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")
        biz_id_str = str(lead_doc.get("business_id"))

        events: List[TimelineEvent] = []

        if lead_doc.get("created_at"):
            events.append(
                TimelineEvent(
                    event_type="DISCOVERED",
                    title="Lead Discovered & Imported",
                    description=f"Source: {lead_doc.get('lead_source', 'MANUAL')}",
                    timestamp=lead_doc.get("created_at"),
                )
            )

        if biz_id_str:
            r_coll = self.research_repo._get_collection()
            r_cursor = r_coll.find({"business_id": self.research_repo.parse_object_id(biz_id_str)}).sort("created_at", 1)
            async for r in r_cursor:
                events.append(
                    TimelineEvent(
                        event_type="RESEARCHED",
                        title="Business Research Recorded",
                        description=f"Confidence: {r.get('confidence_score')}",
                        timestamp=r.get("created_at"),
                    )
                )

            a_coll = self.audit_repo._get_collection()
            a_cursor = a_coll.find({"business_id": self.audit_repo.parse_object_id(biz_id_str)}).sort("created_at", 1)
            async for a in a_cursor:
                events.append(
                    TimelineEvent(
                        event_type="AUDITED",
                        title="Website Audit Performed",
                        description=f"Overall Score: {a.get('overall_score')}/100",
                        timestamp=a.get("created_at"),
                    )
                )

        qual = lead_doc.get("qualification", {})
        if qual.get("qualification_score") is not None:
            events.append(
                TimelineEvent(
                    event_type="QUALIFIED",
                    title="AI Lead Qualification Completed",
                    description=f"Score: {qual.get('qualification_score')}/100",
                    timestamp=lead_doc.get("updated_at") or lead_doc.get("created_at"),
                )
            )

        o_coll = self.outreach_repo._get_collection()
        o_cursor = o_coll.find({"lead_id": self.outreach_repo.parse_object_id(lead_id)}).sort("created_at", 1)
        async for o in o_cursor:
            events.append(
                TimelineEvent(
                    event_type="PITCH_GENERATED",
                    title=f"Pitch Draft Created ({o.get('channel', 'EMAIL')})",
                    description=f"Status: {o.get('status', 'DRAFT')}",
                    timestamp=o.get("created_at"),
                )
            )

        c_coll = self.conversation_repo._get_collection()
        c_cursor = c_coll.find({"lead_id": self.conversation_repo.parse_object_id(lead_id)}).sort("created_at", 1)
        async for c in c_cursor:
            events.append(
                TimelineEvent(
                    event_type="CONVERSATION_UPDATED",
                    title="Communication Record Updated",
                    description=f"Status: {c.get('status')}",
                    timestamp=c.get("updated_at") or c.get("created_at"),
                )
            )

        events.sort(key=lambda x: x.timestamp)
        return LeadTimelineResponse(lead_id=lead_id, events=events)

    async def execute_sales_action(
        self,
        lead_id: str,
        action_type: str,
        force_refresh: bool = False,
        channel: OutreachChannel = OutreachChannel.EMAIL,
    ) -> SalesActionResponse:
        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")

        lead_status = str(lead_doc.get("lead_status", ""))
        if lead_status in ("DO_NOT_CONTACT", "INVALID"):
            raise ValidationError(f"Cannot execute action '{action_type}' on lead in state {lead_status}.")

        action_clean = action_type.strip().upper()

        if action_clean == "RUN_INTELLIGENCE":
            intel_service = LeadIntelligenceService()
            result = await intel_service.process_lead_intelligence(lead_id=lead_id)
            return SalesActionResponse(
                success=True,
                action=action_clean,
                lead_id=lead_id,
                message="Intelligence orchestration completed successfully.",
                result=result.model_dump(mode="json"),
            )
        elif action_clean == "QUALIFY":
            qual_service = LeadQualificationService()
            result = await qual_service.qualify_lead(lead_id=lead_id, force_refresh=force_refresh)
            return SalesActionResponse(
                success=True,
                action=action_clean,
                lead_id=lead_id,
                message="Lead qualification completed successfully.",
                result=result.model_dump(mode="json"),
            )
        elif action_clean == "GENERATE_PITCH":
            pitch_service = PitchGenerationService()
            req = PitchGenerationRequest(channel=channel, force_refresh=force_refresh)
            result = await pitch_service.generate_pitch(lead_id=lead_id, req=req)
            return SalesActionResponse(
                success=True,
                action=action_clean,
                lead_id=lead_id,
                message="Pitch draft generated successfully.",
                result=result.model_dump(mode="json"),
            )
        else:
            raise ValidationError(
                f"Invalid sales action '{action_type}'. Supported actions: RUN_INTELLIGENCE, QUALIFY, GENERATE_PITCH."
            )
