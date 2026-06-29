"""Tests for query orchestration service."""

from unittest.mock import AsyncMock

import pytest

from app.models.clinical_trials import StudiesSearchResult
from app.models.llm import SearchIntent
from app.models.request import UserQuery
from app.services.aggregation_service import AggregationService
from app.services.clinical_trials_service import ClinicalTrialsService
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.services.visualization_service import VisualizationService


@pytest.fixture
def sample_intent() -> SearchIntent:
    return SearchIntent(
        condition="Breast Cancer",
        metric="trial_count",
        group_by="year",
        visualization_hint="time_series",
    )


@pytest.fixture
def query_service(
    sample_intent,
    sample_studies,
) -> tuple[QueryService, AsyncMock, AsyncMock]:
    llm_service = AsyncMock(spec=LLMService)
    clinical_trials_service = AsyncMock(spec=ClinicalTrialsService)
    aggregation_service = AggregationService()
    visualization_service = VisualizationService()

    llm_service.extract_search_intent.return_value = sample_intent
    clinical_trials_service.fetch_studies.return_value = StudiesSearchResult(
        studies=sample_studies,
        pages_fetched=1,
        api_params={"query.cond": "Breast Cancer"},
        latency_ms=120.0,
    )

    service = QueryService(
        llm_service=llm_service,
        clinical_trials_service=clinical_trials_service,
        aggregation_service=aggregation_service,
        visualization_service=visualization_service,
    )
    return service, llm_service, clinical_trials_service


@pytest.mark.asyncio
async def test_process_query_runs_full_pipeline(query_service):
    service, llm_service, clinical_trials_service = query_service
    user_query = UserQuery(
        query="How has the number of breast cancer trials changed over time?"
    )

    response = await service.process_query(user_query)

    assert response.visualization.type == "line_chart"
    assert response.visualization.title == "Breast Cancer Trials Over Time"
    assert response.meta.record_count == 3
    assert response.meta.source == "ClinicalTrials.gov"
    assert len(response.visualization.data) == 3
    assert all("year" in row and "trial_count" in row for row in response.visualization.data)

    llm_service.extract_search_intent.assert_awaited_once_with(user_query)
    clinical_trials_service.fetch_studies.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_query_respects_explicit_filters(query_service):
    service, llm_service, _ = query_service
    user_query = UserQuery(
        query="Trials by phase",
        drug_name="Pembrolizumab",
        trial_phase="Phase 2",
    )

    await service.process_query(user_query)

    llm_service.extract_search_intent.assert_awaited_once_with(user_query)
