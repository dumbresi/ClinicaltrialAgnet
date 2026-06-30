"""Tests for query builder."""

import pytest

from app.core.exceptions import InvalidExecutionPlanError
from app.models.execution_plan import ExecutionPlan, PlanEntity, PlanFilters
from app.services.query_builder import QueryBuilder


def test_single_request_from_filters():
    plan = ExecutionPlan(
        filters=PlanFilters(
            condition="Breast Cancer",
            drug="Pembrolizumab",
            status="RECRUITING",
        ),
        group_by="phase",
        visualization="bar_chart",
    )
    result = QueryBuilder().build(plan)

    assert len(result.requests) == 1
    params = result.requests[0].params
    assert params["query.cond"] == "Breast Cancer"
    assert params["query.intr"] == "Pembrolizumab"
    assert params["filter.overallStatus"] == "RECRUITING"


def test_comparison_creates_multiple_requests():
    plan = ExecutionPlan(
        intent="comparison",
        entities=[
            PlanEntity(type="drug", value="Pembrolizumab"),
            PlanEntity(type="drug", value="Nivolumab"),
        ],
        filters=PlanFilters(status="RECRUITING", country="United States"),
        group_by="phase",
        metric="trial_count",
        visualization="grouped_bar_chart",
        comparison=True,
    )
    result = QueryBuilder().build(plan)

    assert len(result.requests) == 2
    assert result.requests[0].label == "Pembrolizumab"
    assert result.requests[1].label == "Nivolumab"
    assert result.requests[0].params["query.intr"] == "Pembrolizumab"
    assert result.requests[1].params["query.intr"] == "Nivolumab"
    assert result.requests[0].params["filter.overallStatus"] == "RECRUITING"
    assert result.requests[0].params["query.locn"] == "United States"


def test_comparison_country_entities_apply_shared_filters():
    plan = ExecutionPlan(
        intent="comparison",
        entities=[
            PlanEntity(type="country", value="United States"),
            PlanEntity(type="country", value="Canada"),
        ],
        filters=PlanFilters(condition="Breast Cancer", drug="Pembrolizumab"),
        group_by="status",
        metric="trial_count",
        visualization="grouped_bar_chart",
        comparison=True,
    )
    result = QueryBuilder().build(plan)

    assert len(result.requests) == 2
    assert result.requests[0].params["query.locn"] == "United States"
    assert result.requests[1].params["query.locn"] == "Canada"
    assert result.requests[0].params["query.cond"] == "Breast Cancer"
    assert result.requests[0].params["query.intr"] == "Pembrolizumab"


def test_unscoped_summary_kpi_uses_broad_search_term():
    plan = ExecutionPlan(
        intent="summary",
        visualization="kpi",
        metric="trial_count",
    )
    result = QueryBuilder().build(plan)

    assert len(result.requests) == 1
    assert result.requests[0].params["query.term"] == "clinical trial"


def test_missing_search_criteria_raises():
    plan = ExecutionPlan(
        intent="trend",
        group_by="year",
        visualization="line_chart",
    )
    with pytest.raises(InvalidExecutionPlanError):
        QueryBuilder().build(plan)
