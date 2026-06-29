"""Tests for visualization spec generation."""

import pytest

from app.core.exceptions import InvalidVisualizationError
from app.models.aggregation import AggregatedData
from app.models.llm import SearchIntent
from app.services.visualization_service import (
    VisualizationService,
    build_title,
    select_visualization_type,
)


@pytest.fixture
def service() -> VisualizationService:
    return VisualizationService()


def test_select_line_chart_for_year_grouping():
    aggregated = AggregatedData(
        group_by="year",
        metric="trial_count",
        rows=[{"year": 2018, "trial_count": 10}],
        record_count=10,
    )
    intent = SearchIntent(condition="Breast Cancer", group_by="year")

    assert select_visualization_type(aggregated, intent) == "line_chart"


def test_select_bar_chart_for_phase_grouping():
    aggregated = AggregatedData(
        group_by="phase",
        metric="trial_count",
        rows=[{"phase": "Phase 2", "trial_count": 5}],
        record_count=5,
    )
    intent = SearchIntent(condition="Breast Cancer", group_by="phase")

    assert select_visualization_type(aggregated, intent) == "bar_chart"


def test_select_pie_chart_for_proportion_metric():
    aggregated = AggregatedData(
        group_by="status",
        metric="proportion",
        rows=[{"status": "Recruiting", "trial_count": 2, "proportion": 1.0}],
        record_count=2,
    )
    intent = SearchIntent(group_by="status", metric="proportion")

    assert select_visualization_type(aggregated, intent) == "pie_chart"


def test_select_map_for_country_grouping():
    aggregated = AggregatedData(
        group_by="country",
        metric="trial_count",
        rows=[{"country": "United States", "trial_count": 3}],
        record_count=3,
    )
    intent = SearchIntent(condition="Breast Cancer", group_by="country")

    assert select_visualization_type(aggregated, intent) == "map"


def test_network_graph_raises():
    aggregated = AggregatedData(
        group_by="intervention",
        metric="trial_count",
        rows=[{"intervention": "Drug A", "trial_count": 1}],
        record_count=1,
    )
    intent = SearchIntent(
        group_by="intervention",
        visualization_hint="network_graph",
    )

    with pytest.raises(InvalidVisualizationError):
        select_visualization_type(aggregated, intent)


def test_build_title_with_condition_and_drug():
    intent = SearchIntent(
        condition="Breast Cancer",
        drug="Pembrolizumab",
        group_by="phase",
    )
    assert build_title(intent, "bar_chart") == (
        "Trials for Pembrolizumab in Breast Cancer by Phase"
    )


def test_build_spec_line_chart(service):
    aggregated = AggregatedData(
        group_by="year",
        metric="trial_count",
        rows=[
            {"year": 2018, "trial_count": 42},
            {"year": 2019, "trial_count": 51},
        ],
        record_count=93,
    )
    intent = SearchIntent(
        condition="Breast Cancer",
        group_by="year",
        visualization_hint="time_series",
    )

    spec = service.build_spec(aggregated, intent)

    assert spec.type == "line_chart"
    assert spec.title == "Breast Cancer Trials Over Time"
    assert spec.encoding.x is not None
    assert spec.encoding.x.field == "year"
    assert spec.encoding.y is not None
    assert spec.encoding.y.field == "trial_count"
    assert len(spec.data) == 2


def test_build_spec_bar_chart_example_shape(service):
    aggregated = AggregatedData(
        group_by="phase",
        metric="trial_count",
        rows=[
            {"phase": "Phase 1", "trial_count": 32},
            {"phase": "Phase 2", "trial_count": 78},
        ],
        record_count=110,
    )
    intent = SearchIntent(drug="Pembrolizumab", group_by="phase")

    spec = service.build_spec(aggregated, intent)

    assert spec.type == "bar_chart"
    assert spec.encoding.x is not None
    assert spec.encoding.x.field == "phase"
    assert spec.encoding.y is not None
    assert spec.encoding.y.field == "trial_count"


def test_build_response_includes_meta(service):
    aggregated = AggregatedData(
        group_by="phase",
        metric="trial_count",
        rows=[{"phase": "Phase 2", "trial_count": 10}],
        record_count=10,
        notes=["sample note"],
    )
    intent = SearchIntent(
        condition="Breast Cancer",
        drug="Pembrolizumab",
        group_by="phase",
    )

    response = service.build_response(aggregated, intent)

    assert response.visualization.type == "bar_chart"
    assert response.meta.record_count == 10
    assert response.meta.source == "ClinicalTrials.gov"
    assert response.meta.filters["condition"] == "Breast Cancer"
    assert response.meta.filters["drug"] == "Pembrolizumab"
    assert response.meta.filters["group_by"] == "phase"
    assert "sample note" in response.meta.notes


def test_build_spec_empty_rows_raises(service):
    aggregated = AggregatedData(
        group_by="year",
        metric="trial_count",
        rows=[],
        record_count=0,
    )
    intent = SearchIntent(group_by="year")

    with pytest.raises(InvalidVisualizationError):
        service.build_spec(aggregated, intent)
