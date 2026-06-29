"""Tests for query builder."""

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
