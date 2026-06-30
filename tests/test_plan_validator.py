"""Tests for execution plan validation."""

import pytest

from app.core.exceptions import InvalidExecutionPlanError
from app.models.execution_plan import ExecutionPlan, PlanEntity, PlanFilters
from app.services.plan_validator import collect_plan_warnings, validate_execution_plan


def test_actionable_plan_with_filters_passes():
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="year",
        visualization="line_chart",
    )
    validate_execution_plan(plan)
    assert collect_plan_warnings(plan) == []


def test_actionable_plan_with_entities_passes():
    plan = ExecutionPlan(
        intent="comparison",
        entities=[
            PlanEntity(type="drug", value="Pembrolizumab"),
            PlanEntity(type="drug", value="Nivolumab"),
        ],
        group_by="phase",
        visualization="grouped_bar_chart",
        comparison=True,
    )
    validate_execution_plan(plan)


def test_global_kpi_allows_unscoped_search_with_trial_query():
    plan = ExecutionPlan(
        intent="summary",
        visualization="kpi",
        metric="trial_count",
    )
    validate_execution_plan(plan, query_text="How many clinical trials are there?")
    warnings = collect_plan_warnings(plan)
    assert any("broad" in note.lower() for note in warnings)


def test_global_kpi_rejected_for_off_topic_query():
    plan = ExecutionPlan(
        intent="summary",
        visualization="kpi",
        metric="trial_count",
    )
    with pytest.raises(InvalidExecutionPlanError, match="does not appear to be about"):
        validate_execution_plan(plan, query_text="What is the weather?")


def test_network_graph_allows_unscoped_search_with_trial_query():
    plan = ExecutionPlan(
        intent="relationship",
        visualization="network_graph",
        network_source="intervention",
        network_target="sponsor",
    )
    validate_execution_plan(
        plan,
        query_text="Show the relationship between drugs and sponsors",
    )


def test_empty_off_topic_plan_rejected():
    plan = ExecutionPlan(
        intent="trend",
        group_by="year",
        visualization="line_chart",
    )
    with pytest.raises(InvalidExecutionPlanError, match="does not appear to be about"):
        validate_execution_plan(plan)


def test_empty_trend_without_filters_rejected():
    plan = ExecutionPlan(
        intent="single",
        group_by="phase",
        visualization="bar_chart",
    )
    with pytest.raises(InvalidExecutionPlanError):
        validate_execution_plan(plan)


def test_region_country_filter_emits_warning():
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer", country="Europe"),
        group_by="country",
        visualization="map",
    )
    warnings = collect_plan_warnings(plan)
    assert any("region" in warning.lower() for warning in warnings)


def test_execution_plan_has_search_criteria_helpers():
    scoped = ExecutionPlan(filters=PlanFilters(drug="Pembrolizumab"))
    assert scoped.has_search_criteria() is True
    assert scoped.allows_unscoped_search() is False
    assert scoped.is_actionable() is True

    summary = ExecutionPlan(intent="summary", visualization="kpi")
    assert summary.has_search_criteria() is False
    assert summary.allows_unscoped_search() is True
    assert summary.is_actionable() is True
