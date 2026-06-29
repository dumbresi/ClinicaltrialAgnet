"""Tests for ClinicalTrials.gov client helpers and mocked HTTP."""

import json

import httpx
import pytest

from app.clients.clinical_trials_client import (
    ClinicalTrialsClient,
    build_search_params,
    parse_study_record,
)
from app.core.config import Settings
from app.core.exceptions import ClinicalTrialsAPIError, NoStudiesFoundError
from app.models.llm import SearchIntent
from app.services.clinical_trials_service import ClinicalTrialsService
from app.utils.helpers import normalize_phase_token

SAMPLE_STUDY = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT00000001",
            "briefTitle": "Sample Study",
        },
        "statusModule": {
            "overallStatus": "RECRUITING",
            "startDateStruct": {"date": "2021-06-01"},
        },
        "sponsorCollaboratorsModule": {
            "leadSponsor": {"name": "Sample Sponsor"},
        },
        "designModule": {"phases": ["PHASE2"]},
        "contactsLocationsModule": {
            "locations": [{"country": "United States"}, {"country": "Canada"}],
        },
        "armsInterventionsModule": {
            "interventions": [{"name": "Drug A"}, {"name": "Drug B"}],
        },
    }
}


@pytest.fixture
def settings() -> Settings:
    return Settings(
        openai_api_key="test-key",
        clinical_trials_page_size=2,
        clinical_trials_max_pages=3,
    )


def test_normalize_phase_token():
    assert normalize_phase_token("Phase 2") == "PHASE2"
    assert normalize_phase_token("phase3") == "PHASE3"
    assert normalize_phase_token("unknown") is None


def test_build_search_params_from_intent():
    intent = SearchIntent(
        condition="Breast Cancer",
        drug="Pembrolizumab",
        sponsor="NIH",
        country="United States",
        status="RECRUITING",
        phase="Phase 2",
        start_year=2018,
        end_year=2025,
    )
    params = build_search_params(intent)

    assert params["query.cond"] == "Breast Cancer"
    assert params["query.intr"] == "Pembrolizumab"
    assert params["query.spons"] == "NIH"
    assert params["query.locn"] == "United States"
    assert params["filter.overallStatus"] == "RECRUITING"
    assert "AREA[Phase]PHASE2" in params["filter.advanced"]
    assert "AREA[StartDate]RANGE[2018-01-01,2025-12-31]" in params["filter.advanced"]
    assert "fields" in params


def test_build_search_params_fallback_term():
    intent = SearchIntent()
    params = build_search_params(intent)
    assert params["query.term"] == "clinical trial"


def test_parse_study_record():
    record = parse_study_record(SAMPLE_STUDY)
    assert record.nct_id == "NCT00000001"
    assert record.overall_status == "RECRUITING"
    assert record.start_date == "2021-06-01"
    assert record.phases == ["PHASE2"]
    assert record.sponsor == "Sample Sponsor"
    assert record.countries == ["United States", "Canada"]
    assert record.interventions == ["Drug A", "Drug B"]


@pytest.mark.asyncio
async def test_search_studies_pagination_mock(settings):
    page_one = {
        "studies": [SAMPLE_STUDY],
        "nextPageToken": "token-2",
    }
    page_two = {
        "studies": [
            {
                **SAMPLE_STUDY,
                "protocolSection": {
                    **SAMPLE_STUDY["protocolSection"],
                    "identificationModule": {
                        **SAMPLE_STUDY["protocolSection"]["identificationModule"],
                        "nctId": "NCT00000002",
                    },
                },
            }
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("pageToken") == "token-2":
            return httpx.Response(200, json=page_two)
        return httpx.Response(200, json=page_one)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=settings.clinical_trials_base_url_str,
    ) as http_client:
        client = ClinicalTrialsClient(settings, http_client=http_client)
        result = await client.search_studies(
            SearchIntent(condition="Breast Cancer"),
            page_size=1,
            max_pages=2,
        )

    assert len(result.studies) == 2
    assert result.pages_fetched == 2
    assert {study.nct_id for study in result.studies} == {
        "NCT00000001",
        "NCT00000002",
    }


@pytest.mark.asyncio
async def test_get_study_mock(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/studies/NCT00000001")
        return httpx.Response(200, json=SAMPLE_STUDY)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=settings.clinical_trials_base_url_str,
    ) as http_client:
        client = ClinicalTrialsClient(settings, http_client=http_client)
        record = await client.get_study("nct00000001")

    assert record.nct_id == "NCT00000001"


@pytest.mark.asyncio
async def test_api_error_is_mapped(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="`filter.phase` is unknown parameter")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=settings.clinical_trials_base_url_str,
    ) as http_client:
        client = ClinicalTrialsClient(settings, http_client=http_client)
        with pytest.raises(ClinicalTrialsAPIError):
            await client.search_studies(SearchIntent(condition="Breast Cancer"))


@pytest.mark.asyncio
async def test_service_raises_when_no_studies(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"studies": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=settings.clinical_trials_base_url_str,
    ) as http_client:
        client = ClinicalTrialsClient(settings, http_client=http_client)
        service = ClinicalTrialsService(client)
        with pytest.raises(NoStudiesFoundError):
            await service.fetch_studies(SearchIntent(condition="Breast Cancer"))
