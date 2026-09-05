import re
from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.business import BusinessRepository
from app.schemas.api import BusinessCreateRequest, BusinessUpdateRequest, PaginationMetadata
from app.schemas.business import Business, SocialProfiles
from app.schemas.common import utc_now


def extract_domain(url_or_domain: Optional[str]) -> Optional[str]:
    if not url_or_domain:
        return None
    val = url_or_domain.strip().lower()
    val = re.sub(r"^https?://", "", val)
    val = re.sub(r"^www\.", "", val)
    val = val.split("/")[0].split("?")[0]
    return val if val else None


def normalize_phone_num(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits if digits else None


class BusinessService:
    def __init__(self, business_repo: Optional[BusinessRepository] = None):
        self.repo = business_repo or BusinessRepository()

    async def create_business(self, req: BusinessCreateRequest) -> Business:
        norm_name = req.name.strip().lower()
        norm_domain = extract_domain(req.website)
        norm_phone = normalize_phone_num(req.phone)

        # Duplicate detection logic
        if norm_domain:
            existing = await self.repo.get_by_domain(norm_domain)
            if existing:
                raise ConflictError(f"A business with domain '{norm_domain}' already exists.")

        if norm_name and norm_phone:
            existing = await self.repo.get_by_normalized_phone(norm_phone)
            if existing and existing.get("normalized_name") == norm_name:
                raise ConflictError(f"A business with name '{req.name}' and phone number already exists.")

        biz_obj = Business(
            name=req.name,
            normalized_name=norm_name,
            description=req.description,
            category=req.category,
            sub_category=req.sub_category,
            address=req.address,
            city=req.city,
            state=req.state,
            country=req.country,
            postal_code=req.postal_code,
            website=req.website,
            normalized_domain=norm_domain,
            phone=req.phone,
            normalized_phone=norm_phone,
            email=req.email,
            social_profiles=req.social_profiles or SocialProfiles(),
            source_records=req.source_records,
            business_status=req.business_status,
            verification_status=req.verification_status,
        )

        doc = biz_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.repo.create(doc)
        return Business(**created_doc)

    async def get_business(self, business_id: str) -> Business:
        doc = await self.repo.get_by_id(business_id)
        if not doc:
            raise NotFoundError(f"Business with ID '{business_id}' not found.")
        return Business(**doc)

    async def list_businesses(
        self,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        verification_status: Optional[str] = None,
        business_status: Optional[str] = None,
    ) -> Tuple[List[Business], PaginationMetadata]:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        skip = (page - 1) * page_size

        query: Dict[str, Any] = {}
        if search:
            query["normalized_name"] = {"$regex": search.strip().lower(), "$options": "i"}
        if city:
            query["city"] = {"$regex": city.strip(), "$options": "i"}
        if state:
            query["state"] = {"$regex": state.strip(), "$options": "i"}
        if country:
            query["country"] = {"$regex": country.strip(), "$options": "i"}
        if verification_status:
            query["verification_status"] = verification_status
        if business_status:
            query["business_status"] = business_status

        items_docs, total = await self.repo.list_businesses(query, skip, page_size)
        pages = (total + page_size - 1) // page_size if total > 0 else 1

        businesses = [Business(**d) for d in items_docs]
        meta = PaginationMetadata(page=page, page_size=page_size, total=total, pages=pages)
        return businesses, meta

    async def update_business(self, business_id: str, req: BusinessUpdateRequest) -> Business:
        existing = await self.repo.get_by_id(business_id)
        if not existing:
            raise NotFoundError(f"Business with ID '{business_id}' not found.")

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return Business(**existing)

        if "name" in update_data and update_data["name"]:
            update_data["normalized_name"] = update_data["name"].strip().lower()
        if "website" in update_data and update_data["website"]:
            update_data["normalized_domain"] = extract_domain(update_data["website"])
        if "phone" in update_data and update_data["phone"]:
            update_data["normalized_phone"] = normalize_phone_num(update_data["phone"])

        update_data["updated_at"] = utc_now()

        updated_doc = await self.repo.update_by_id(business_id, update_data)
        return Business(**updated_doc)
