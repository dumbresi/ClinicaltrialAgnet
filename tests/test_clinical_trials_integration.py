"""Live integration tests against ClinicalTrials.gov API."""

import pytest

from app.clients.clinical_trials_client import ClinicalTrialsClient
from app.core.config import Settings
from app.core.exceptions import NoStudiesFoundError
from app.models.llm import SearchIntent
from app.services.clinical_trials_service import ClinicalTrialsService

pytestmark = pytest.mark.integration


@pytest.fixture
def settings() -> Settings:
    return Settings(
        openai_api_key="test-key",
        clinical_trials_page_size=5,
        clinical_trials_max_pages=2,
    )


@pytest.fixture
async def client(settings):
    clinical_trials_client = ClinicalTrialsClient(settings)
    yield clinical_trials_client
    await clinical_trials_client.aclose()


@pytest.mark.asyncio
async def test_live_search_breast_cancer(client):
    intent = SearchIntent(condition="Breast Cancer", status="RECRUITING")
    result = await client.search_studies(intent, page_size=5, max_pages=1)

    assert result.pages_fetched == 1
    assert len(result.studies) > 0
    assert result.studies[0].nct_id.startswith("NCT")
    assert "query.cond" in result.api_params
    assert result.latency_ms > 0


@pytest.mark.asyncio
async def test_live_get_study(client):
    search = await client.search_studies(
        SearchIntent(condition="Breast Cancer"),
        page_size=1,
        max_pages=1,
    )
    nct_id = search.studies[0].nct_id

    record = await client.get_study(nct_id)

    assert record.nct_id == nct_id
    assert record.brief_title


@pytest.mark.asyncio
async def test_live_pagination(client):
    intent = SearchIntent(condition="Breast Cancer")
    result = await client.search_studies(intent, page_size=2, max_pages=2)

    assert result.pages_fetched == 2
    assert len(result.studies) >= 3
    assert len({study.nct_id for study in result.studies}) == len(result.studies)


@pytest.mark.asyncio
async def test_live_service_fetch_studies(client):
    service = ClinicalTrialsService(client)
    result = await service.fetch_studies(
        SearchIntent(
            condition="Breast Cancer",
            drug="Pembrolizumab",
            group_by="year",
        )
    )

    assert len(result.studies) > 0


@pytest.mark.asyncio
async def test_live_no_studies_found(client):
    service = ClinicalTrialsService(client)
    with pytest.raises(NoStudiesFoundError):
        await service.fetch_studies(
            SearchIntent(condition="ThisConditionDoesNotExist99999")
        )
