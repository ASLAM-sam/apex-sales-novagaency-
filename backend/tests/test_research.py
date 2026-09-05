import pytest
from unittest.mock import AsyncMock, MagicMock

from app.research.extractor import (
    extract_deterministic_research,
    extract_headings,
    extract_meta_description,
)
from app.research.service import ResearchService
from app.schemas.business import Business
from app.verification.models import WebsiteFetchResult


def test_html_extraction_helpers():
    html = """
    <html>
      <head>
        <title>TechNova Solutions - Custom Software Development</title>
        <meta name="description" content="We build modern cloud software and mobile applications.">
      </head>
      <body>
        <h1>Our Core Software Services</h1>
        <h2>Web Development Solutions</h2>
        <h2>Cloud Maintenance Services</h2>
        <p>Contact us for custom agency work.</p>
      </body>
    </html>
    """
    meta = extract_meta_description(html)
    assert meta == "We build modern cloud software and mobile applications."

    headings = extract_headings(html)
    assert "Our Core Software Services" in headings
    assert "Web Development Solutions" in headings

    res = extract_deterministic_research(
        business_name="TechNova Solutions",
        category="Software",
        city="Austin",
        html=html,
        title="TechNova Solutions",
    )
    assert "TechNova Solutions" in res["business_summary"]
    assert "Austin" in res["location_summary"]
    assert len(res["products_services"]) > 0


@pytest.mark.asyncio
async def test_research_service_upsert():
    mock_research_repo = MagicMock()
    mock_research_repo.parse_object_id = MagicMock(side_effect=lambda x: x)
    mock_research_repo.get_by_business_id = AsyncMock(return_value=[])

    created_doc = {
        "_id": "507f1f77bcf86cd799439099",
        "business_id": "507f1f77bcf86cd799439011",
        "business_summary": "Summary",
        "products_services": ["Software"],
        "location_summary": "Austin",
        "research_sources": [],
        "research_version": "1.0",
    }
    mock_research_repo.create = AsyncMock(return_value=created_doc)

    svc = ResearchService(research_repo=mock_research_repo)
    biz = Business(
        id="507f1f77bcf86cd799439011",
        name="TechNova",
        category="Software",
        city="Austin",
        website="https://technova.io",
    )
    fetch_res = WebsiteFetchResult(
        accessible=True,
        final_url="https://technova.io",
        title="TechNova - Software Agency",
        html_content="<h1>Software Agency</h1>",
    )

    rec = await svc.perform_research(business=biz, fetch_result=fetch_res)
    assert rec.business_summary is not None
    mock_research_repo.create.assert_called_once()
