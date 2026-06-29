"""End-to-end pipeline tests with mocked external services."""

from unittest.mock import AsyncMock

import pytest

from app.aggregation.context import TaggedStudy
from app.models.clinical_trials import MultiSearchResult, StudiesSearchResult
from app.models.execution_plan import ExecutionPlan, PlanEntity, PlanFilters
from app.models.request import UserQuery
from app.services.aggregation_service import AggregationService
from app.services.clinical_trials_service import ClinicalTrialsService
from app.services.query_planner_service import QueryPlannerService
from app.services.query_service import QueryService
from app.services.visualization_service import VisualizationService


@pytest.mark.asyncio
async def test_pipeline_bar_chart_by_phase(sample_studies):
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="phase",
        metric="trial_count",
        visualization="bar_chart",
    )
    service = _build_service(sample_studies, plan)
    user_query = UserQuery(query="Show breast cancer trials by phase")

    response = await service.process_query(user_query)

    assert response.visualization.type == "bar_chart"
    assert response.visualization.encoding.x is not None
    assert response.visualization.encoding.x.field == "phase"
    assert response.meta.filters["group_by"] == "phase"


@pytest.mark.asyncio
async def test_pipeline_pie_chart_status_proportion(sample_studies):
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="status",
        metric="proportion",
        visualization="pie_chart",
    )
    service = _build_service(sample_studies, plan)
    user_query = UserQuery(query="What share of breast cancer trials are recruiting?")

    response = await service.process_query(user_query)

    assert response.visualization.type == "pie_chart"
    assert response.visualization.encoding.value is not None
    assert response.visualization.encoding.value.field == "proportion"
    assert round(sum(row["proportion"] for row in response.visualization.data), 4) == 1.0


@pytest.mark.asyncio
async def test_pipeline_map_by_country(sample_studies):
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="country",
        metric="trial_count",
        visualization="map",
    )
    service = _build_service(sample_studies, plan)
    user_query = UserQuery(query="Breast cancer trials by country")

    response = await service.process_query(user_query)

    assert response.visualization.type == "map"
    assert response.visualization.encoding.geo is not None
    assert response.visualization.encoding.geo.field == "country"


@pytest.mark.asyncio
async def test_pipeline_comparison_by_phase(sample_studies):
    plan = ExecutionPlan(
        intent="comparison",
        entities=[
            PlanEntity(type="drug", value="Pembrolizumab"),
            PlanEntity(type="drug", value="Nivolumab"),
        ],
        group_by="phase",
        metric="trial_count",
        visualization="grouped_bar_chart",
        comparison=True,
    )
    service = _build_service(sample_studies, plan, comparison=True)
    user_query = UserQuery(query="Compare Pembrolizumab and Nivolumab trials by phase")

    response = await service.process_query(user_query)

    assert response.visualization.type == "grouped_bar_chart"
    assert response.visualization.encoding.series is not None
    assert response.meta.api_calls == 2


def _build_service(studies: list, plan: ExecutionPlan, *, comparison: bool = False) -> QueryService:
    planner_service = AsyncMock(spec=QueryPlannerService)
    clinical_trials_service = AsyncMock(spec=ClinicalTrialsService)
    planner_service.create_execution_plan.return_value = plan

    if comparison:
        half = max(1, len(studies) // 2)
        results = [
            StudiesSearchResult(
                studies=studies[:half],
                pages_fetched=1,
                api_params={"query.intr": "Pembrolizumab"},
                latency_ms=50.0,
                label="Pembrolizumab",
            ),
            StudiesSearchResult(
                studies=studies[half:],
                pages_fetched=1,
                api_params={"query.intr": "Nivolumab"},
                latency_ms=50.0,
                label="Nivolumab",
            ),
        ]
        tagged = [
            TaggedStudy(study=s, series="Pembrolizumab", series_field="drug")
            for s in studies[:half]
        ] + [
            TaggedStudy(study=s, series="Nivolumab", series_field="drug")
            for s in studies[half:]
        ]
    else:
        results = [
            StudiesSearchResult(
                studies=studies,
                pages_fetched=1,
                api_params={"query.cond": plan.filters.condition or "clinical trial"},
                latency_ms=50.0,
                label="all",
            )
        ]
        tagged = [TaggedStudy(study=study) for study in studies]

    clinical_trials_service.fetch_studies.return_value = MultiSearchResult(
        results=results,
        api_calls=len(results),
        studies_processed=len(studies),
        total_latency_ms=50.0 * len(results),
    )
    clinical_trials_service.tag_studies.return_value = tagged

    return QueryService(
        query_planner_service=planner_service,
        clinical_trials_service=clinical_trials_service,
        aggregation_service=AggregationService(),
        visualization_service=VisualizationService(),
    )
