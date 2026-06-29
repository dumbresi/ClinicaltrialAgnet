"""Tests for visualization spec generation."""

import pytest

from app.core.exceptions import InvalidVisualizationError
from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan, PlanEntity, PlanFilters
from app.services.visualization_service import VisualizationService
from app.visualization.builders.base import build_title


@pytest.fixture
def service() -> VisualizationService:
    return VisualizationService()


def test_build_title_comparison():
    plan = ExecutionPlan(
        intent="comparison",
        entities=[
            PlanEntity(type="drug", value="Pembrolizumab"),
            PlanEntity(type="drug", value="Nivolumab"),
        ],
        group_by="phase",
        comparison=True,
        visualization="grouped_bar_chart",
    )
    assert build_title(plan) == "Pembrolizumab vs Nivolumab Trials by Phase"


def test_build_spec_grouped_bar_chart(service):
    aggregated = AggregatedData(
        group_by="drug+phase",
        metric="trial_count",
        rows=[
            {"drug": "Pembrolizumab", "phase": "Phase 1", "trial_count": 120},
            {"drug": "Nivolumab", "phase": "Phase 1", "trial_count": 95},
        ],
        record_count=215,
        comparison=True,
        series_field="drug",
    )
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

    spec = service.build_spec(aggregated, plan)

    assert spec.type == "grouped_bar_chart"
    assert spec.encoding.x is not None
    assert spec.encoding.x.field == "phase"
    assert spec.encoding.y is not None
    assert spec.encoding.y.field == "trial_count"
    assert spec.encoding.series is not None
    assert spec.encoding.series.field == "drug"


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
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="year",
        visualization="line_chart",
    )

    spec = service.build_spec(aggregated, plan)

    assert spec.type == "line_chart"
    assert spec.encoding.x is not None
    assert spec.encoding.x.field == "year"
    assert spec.encoding.y is not None
    assert spec.encoding.y.field == "trial_count"


def test_build_spec_map(service):
    aggregated = AggregatedData(
        group_by="country",
        metric="trial_count",
        rows=[{"country": "United States", "trial_count": 3}],
        record_count=3,
    )
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="country",
        visualization="map",
    )

    spec = service.build_spec(aggregated, plan)

    assert spec.type == "map"
    assert spec.encoding.geo is not None
    assert spec.encoding.geo.field == "country"


def test_build_response_includes_meta(service):
    aggregated = AggregatedData(
        group_by="phase",
        metric="trial_count",
        rows=[{"phase": "Phase 2", "trial_count": 10}],
        record_count=10,
        notes=["sample note"],
    )
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer", drug="Pembrolizumab"),
        group_by="phase",
        visualization="bar_chart",
    )

    response = service.build_response(
        aggregated,
        plan,
        api_calls=2,
        studies_processed=100,
    )

    assert response.visualization.type == "bar_chart"
    assert response.meta.api_calls == 2
    assert response.meta.studies_processed == 100
    assert response.meta.records_after_filter == 10
    assert response.meta.filters["condition"] == "Breast Cancer"
    assert response.meta.query_plan["group_by"] == "phase"
    assert "sample note" in response.meta.notes
    assert response.meta.generated_at


def test_build_spec_empty_rows_raises(service):
    aggregated = AggregatedData(
        group_by="year",
        metric="trial_count",
        rows=[],
        record_count=0,
    )
    plan = ExecutionPlan(group_by="year", visualization="line_chart")

    with pytest.raises(InvalidVisualizationError):
        service.build_spec(aggregated, plan)


def test_build_spec_network_graph(service):
    aggregated = AggregatedData(
        group_by="none",
        metric="trial_count",
        rows=[
            {"source": "Phase 2", "target": "AstraZeneca", "trial_count": 57},
            {"source": "Phase 1", "target": "Pfizer", "trial_count": 64},
        ],
        record_count=121,
    )
    plan = ExecutionPlan(
        intent="relationship",
        filters=PlanFilters(condition="lung cancer"),
        metric="trial_count",
        visualization="network_graph",
        network_source="phase",
        network_target="sponsor",
    )

    spec = service.build_spec(aggregated, plan)

    assert spec.type == "network_graph"
    assert spec.title == "Lung Cancer Trials: Phase & Sponsor"
    assert spec.encoding.source is not None
    assert spec.encoding.source.label == "Phase"
    assert spec.encoding.target is not None
    assert spec.encoding.target.label == "Sponsor"
    assert spec.encoding.value is not None
    assert spec.encoding.value.label == "Trial Count"
