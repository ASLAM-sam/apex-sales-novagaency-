import logging
from typing import Optional, Tuple
from app.repositories.business import BusinessRepository
from app.schemas.business import Business
from app.schemas.enums import VerificationStatus
from app.verification.models import VerificationResult, WebsiteFetchResult
from app.verification.sources.website import SafeWebsiteFetcher
from app.verification.validators import evaluate_business_verification

logger = logging.getLogger(__name__)


class VerificationService:
    def __init__(
        self,
        business_repo: Optional[BusinessRepository] = None,
        website_fetcher: Optional[SafeWebsiteFetcher] = None,
    ):
        self.business_repo = business_repo or BusinessRepository()
        self.website_fetcher = website_fetcher or SafeWebsiteFetcher()

    async def verify_business(
        self, business: Business, pre_fetched_result: Optional[WebsiteFetchResult] = None
    ) -> Tuple[VerificationResult, Optional[WebsiteFetchResult]]:
        fetch_result = pre_fetched_result

        # Safely attempt fetching website if present and no prefetched result
        if not fetch_result and business.website:
            try:
                fetch_result = await self.website_fetcher.fetch(
                    raw_url=business.website,
                    business_name=business.name,
                    expected_domain=business.normalized_domain,
                )
            except Exception as e:
                logger.error(f"Error fetching website '{business.website}' for verification: {e}")
                fetch_result = WebsiteFetchResult(accessible=False, error_message=str(e))

        result = evaluate_business_verification(business, fetch_result)

        # Update business in DB with computed verification status if changed
        if business.id and business.verification_status != result.verification_status:
            try:
                await self.business_repo.update_by_id(
                    str(business.id), {"verification_status": result.verification_status.value}
                )
                business.verification_status = result.verification_status
            except Exception as e:
                logger.error(f"Failed to update verification status for business {business.id}: {e}")

        return result, fetch_result
