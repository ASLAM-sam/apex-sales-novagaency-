from typing import Any, Dict, Optional
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.research import ResearchRepository
from app.repositories.website_audit import WebsiteAuditRepository
from app.schemas.business import Business
from app.schemas.lead import Lead
from app.schemas.research import Research
from app.schemas.website_audit import WebsiteAudit


class LeadAIContextBuilder:
    """
    Constructs compact, sanitized JSON context objects for AI models.
    Filters raw HTML, credentials, internal IDs to conserve tokens and enforce boundaries.
    """

    def __init__(
        self,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        research_repo: Optional[ResearchRepository] = None,
        audit_repo: Optional[WebsiteAuditRepository] = None,
    ):
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.research_repo = research_repo or ResearchRepository()
        self.audit_repo = audit_repo or WebsiteAuditRepository()

    async def build_context(self, lead_id: str) -> Dict[str, Any]:
        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise ValueError(f"Lead with ID '{lead_id}' not found.")
        lead = Lead(**lead_doc)

        biz_id_str = str(lead.business_id)
        biz_doc = await self.business_repo.get_by_id(biz_id_str)
        if not biz_doc:
            raise ValueError(f"Business with ID '{biz_id_str}' not found.")
        business = Business(**biz_doc)

        research_docs = await self.research_repo.get_by_lead_id(lead_id)
        if not research_docs:
            research_docs = await self.research_repo.get_by_business_id(biz_id_str)
        latest_research = Research(**research_docs[0]) if research_docs else None

        audit_doc = await self.audit_repo.get_latest_for_business(biz_id_str)
        if not audit_doc:
            audit_docs = await self.audit_repo.get_by_lead_id(lead_id)
            audit_doc = audit_docs[0] if audit_docs else None
        latest_audit = WebsiteAudit(**audit_doc) if audit_doc else None

        loc_parts = [business.city, business.state, business.country]
        loc_str = ", ".join([p for p in loc_parts if p])

        biz_summary = {
            "name": business.name,
            "category": business.category or "Unknown",
            "location": loc_str or "Unknown",
            "website": business.website or "None",
            "phone": business.phone or "None",
            "email": business.email or "None",
            "status": (
                business.business_status.value
                if hasattr(business.business_status, "value")
                else str(business.business_status)
            ),
        }

        v_summary = {
            "verification_status": (
                business.verification_status.value
                if hasattr(business.verification_status, "value")
                else str(business.verification_status)
            ),
            "has_phone": bool(business.phone),
            "has_email": bool(business.email),
            "has_website": bool(business.website),
        }

        res_desc = latest_research.description_snippet if latest_research else None
        if res_desc and len(res_desc) > 250:
            res_desc = res_desc[:250] + "..."

        res_summary = {
            "has_research": latest_research is not None,
            "services": latest_research.extracted_services if latest_research else [],
            "products": latest_research.extracted_products if latest_research else [],
            "target_audience": latest_research.target_audience if latest_research else [],
            "description": res_desc or "None",
        }

        audit_summary = {
            "has_audit": latest_audit is not None,
            "overall_score": latest_audit.overall_score if latest_audit else None,
            "is_https": latest_audit.is_https if latest_audit else None,
            "issues": [
                {
                    "issue_type": issue.issue_type.value if hasattr(issue.issue_type, "value") else str(issue.issue_type),
                    "title": issue.title,
                    "severity": issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity),
                }
                for issue in (latest_audit.issues if latest_audit else [])
            ],
        }

        return {
            "lead": {
                "lead_id": lead_id,
                "lead_status": lead.lead_status.value if hasattr(lead.lead_status, "value") else str(lead.lead_status),
                "contact_name": lead.contact.name if lead.contact else None,
                "contact_email": lead.contact.email if lead.contact else None,
            },
            "business": biz_summary,
            "verification": v_summary,
            "research": res_summary,
            "website_audit": audit_summary,
        }
