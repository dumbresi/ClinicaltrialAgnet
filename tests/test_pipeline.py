"""End-to-end pipeline tests with mocked external services."""

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


@pytest.mark.asyncio
async def test_pipeline_bar_chart_by_phase(sample_studies):
    intent = SearchIntent(
        condition="Breast Cancer",
        group_by="phase",
        metric="trial_count",
        visualization_hint="bar_chart",
    )
    service = _build_service(sample_studies, intent)
    user_query = UserQuery(query="Show breast cancer trials by phase")

    response = await service.process_query(user_query)

    assert response.visualization.type == "bar_chart"
    assert response.visualization.encoding.x is not None
    assert response.visualization.encoding.x.field == "phase"
    assert response.meta.filters["group_by"] == "phase"


@pytest.mark.asyncio
async def test_pipeline_pie_chart_status_proportion(sample_studies):
    intent = SearchIntent(
        condition="Breast Cancer",
        group_by="status",
        metric="proportion",
        visualization_hint="pie_chart",
    )
    service = _build_service(sample_studies, intent)
    user_query = UserQuery(query="What share of breast cancer trials are recruiting?")

    response = await service.process_query(user_query)

    assert response.visualization.type == "pie_chart"
    assert response.visualization.encoding.value is not None
    assert response.visualization.encoding.value.field == "proportion"
    assert round(sum(row["proportion"] for row in response.visualization.data), 4) == 1.0


@pytest.mark.asyncio
async def test_pipeline_map_by_country(sample_studies):
    intent = SearchIntent(
        condition="Breast Cancer",
        group_by="country",
        metric="trial_count",
        visualization_hint="map",
    )
    service = _build_service(sample_studies, intent)
    user_query = UserQuery(query="Breast cancer trials by country")

    response = await service.process_query(user_query)

    assert response.visualization.type == "map"
    assert response.visualization.encoding.geo is not None
    assert response.visualization.encoding.geo.field == "country"


def _build_service(studies: list, intent: SearchIntent) -> QueryService:
    llm_service = AsyncMock(spec=LLMService)
    clinical_trials_service = AsyncMock(spec=ClinicalTrialsService)
    llm_service.extract_search_intent.return_value = intent
    clinical_trials_service.fetch_studies.return_value = StudiesSearchResult(
        studies=studies,
        pages_fetched=1,
        api_params={"query.cond": intent.condition or "clinical trial"},
        latency_ms=50.0,
    )
    return QueryService(
        llm_service=llm_service,
        clinical_trials_service=clinical_trials_service,
        aggregation_service=AggregationService(),
        visualization_service=VisualizationService(),
    )
