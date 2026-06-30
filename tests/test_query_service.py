"""Tests for query orchestration service."""

from unittest.mock import AsyncMock

import pytest

from app.aggregation.context import TaggedStudy
from app.models.clinical_trials import MultiSearchResult, StudiesSearchResult
from app.models.execution_plan import ExecutionPlan, PlanFilters
from app.models.request import UserQuery
from app.services.aggregation_service import AggregationService
from app.services.clinical_trials_service import ClinicalTrialsService
from app.services.query_planner_service import QueryPlannerService
from app.services.query_service import QueryService
from app.services.visualization_service import VisualizationService


@pytest.fixture
def sample_plan() -> ExecutionPlan:
    return ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        metric="trial_count",
        group_by="year",
        visualization="line_chart",
        intent="trend",
    )


@pytest.fixture
def query_service(
    sample_plan,
    sample_studies,
) -> tuple[QueryService, AsyncMock, AsyncMock]:
    planner_service = AsyncMock(spec=QueryPlannerService)
    clinical_trials_service = AsyncMock(spec=ClinicalTrialsService)
    aggregation_service = AggregationService()
    visualization_service = VisualizationService()

    planner_service.create_execution_plan.return_value = (sample_plan, [])
    clinical_trials_service.fetch_studies.return_value = MultiSearchResult(
        results=[
            StudiesSearchResult(
                studies=sample_studies,
                pages_fetched=1,
                api_params={"query.cond": "Breast Cancer"},
                latency_ms=120.0,
                label="all",
            )
        ],
        api_calls=1,
        studies_processed=len(sample_studies),
        total_latency_ms=120.0,
    )
    clinical_trials_service.tag_studies.return_value = [
        TaggedStudy(study=study) for study in sample_studies
    ]

    service = QueryService(
        query_planner_service=planner_service,
        clinical_trials_service=clinical_trials_service,
        aggregation_service=aggregation_service,
        visualization_service=visualization_service,
    )
    return service, planner_service, clinical_trials_service


@pytest.mark.asyncio
async def test_process_query_runs_full_pipeline(query_service):
    service, planner_service, clinical_trials_service = query_service
    user_query = UserQuery(
        query="How has the number of breast cancer trials changed over time?"
    )

    response = await service.process_query(user_query)

    assert response.visualization.type == "line_chart"
    assert response.meta.studies_processed == 3
    assert response.meta.api_calls == 1
    assert len(response.visualization.data) == 3
    assert all("year" in row and "trial_count" in row for row in response.visualization.data)

    planner_service.create_execution_plan.assert_awaited_once_with(user_query)
    clinical_trials_service.fetch_studies.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_query_respects_explicit_filters(query_service):
    service, planner_service, _ = query_service
    user_query = UserQuery(
        query="Trials by phase",
        drug_name="Pembrolizumab",
        trial_phase="Phase 2",
    )

    await service.process_query(user_query)

    planner_service.create_execution_plan.assert_awaited_once_with(user_query)
