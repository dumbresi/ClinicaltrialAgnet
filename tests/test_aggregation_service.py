"""Tests for study aggregation."""

import pytest

from app.aggregation.context import AggregationContext, TaggedStudy
from app.aggregation.operations.group_by import GroupByOperation
from app.aggregation.operations.proportion import ProportionOperation
from app.models.aggregation import AggregationOptions
from app.models.clinical_trials import StudyRecord
from app.models.execution_plan import AggregationStep, ExecutionPlan, PlanEntity, PlanFilters
from app.services.aggregation_service import AggregationService


@pytest.fixture
def studies() -> list[StudyRecord]:
    return [
        StudyRecord(
            nct_id="NCT00000001",
            overall_status="RECRUITING",
            start_date="2018-03-01",
            phases=["PHASE2"],
            sponsor="Sponsor A",
            countries=["United States"],
            interventions=["Drug A"],
        ),
        StudyRecord(
            nct_id="NCT00000002",
            overall_status="COMPLETED",
            start_date="2019-07-15",
            phases=["PHASE2", "PHASE3"],
            sponsor="Sponsor B",
            countries=["United States", "Canada"],
            interventions=["Drug A", "Drug B"],
        ),
        StudyRecord(
            nct_id="NCT00000003",
            overall_status="RECRUITING",
            start_date="2020-01-01",
            phases=["PHASE3"],
            sponsor="Sponsor A",
            countries=["France"],
            interventions=["Drug C"],
        ),
        StudyRecord(
            nct_id="NCT00000004",
            overall_status="UNKNOWN",
            start_date=None,
            phases=[],
            sponsor=None,
            countries=[],
            interventions=[],
        ),
    ]


def test_group_by_year(studies):
    tagged = [TaggedStudy(study=study) for study in studies]
    ctx = AggregationContext(
        studies=tagged,
        plan=ExecutionPlan(group_by="year", metric="trial_count", visualization="line_chart"),
    )
    rows = GroupByOperation().apply(
        ctx,
        [],
        AggregationStep(operation="group_by", params={"fields": ["year"]}),
    )
    years = {row["year"]: row["trial_count"] for row in rows}
    assert years[2018] == 1
    assert years[2019] == 1
    assert years[2020] == 1


def test_group_by_country_counts_unique_studies():
    study = StudyRecord(
        nct_id="NCT00000099",
        countries=["United States", "United States", "United States"],
    )
    tagged = [TaggedStudy(study=study)]
    ctx = AggregationContext(
        studies=tagged,
        plan=ExecutionPlan(group_by="country", metric="trial_count", visualization="map"),
    )
    rows = GroupByOperation().apply(
        ctx,
        [],
        AggregationStep(operation="group_by", params={"fields": ["country"]}),
    )
    assert rows == [{"country": "United States", "trial_count": 1}]


def test_comparison_group_by_phase():
    studies = [
        TaggedStudy(
            study=StudyRecord(nct_id="NCT1", phases=["PHASE1"]),
            series="Pembrolizumab",
            series_field="drug",
        ),
        TaggedStudy(
            study=StudyRecord(nct_id="NCT2", phases=["PHASE1", "PHASE2"]),
            series="Pembrolizumab",
            series_field="drug",
        ),
        TaggedStudy(
            study=StudyRecord(nct_id="NCT3", phases=["PHASE1"]),
            series="Nivolumab",
            series_field="drug",
        ),
    ]
    plan = ExecutionPlan(
        intent="comparison",
        entities=[
            PlanEntity(type="drug", value="Pembrolizumab"),
            PlanEntity(type="drug", value="Nivolumab"),
        ],
        metric="trial_count",
        group_by="phase",
        visualization="grouped_bar_chart",
        comparison=True,
    )
    service = AggregationService()
    result = service.aggregate(studies, plan)

    pemb_phase1 = next(
        row for row in result.rows if row["drug"] == "Pembrolizumab" and row["phase"] == "Phase 1"
    )
    nivo_phase1 = next(
        row for row in result.rows if row["drug"] == "Nivolumab" and row["phase"] == "Phase 1"
    )
    assert pemb_phase1["trial_count"] == 2
    assert nivo_phase1["trial_count"] == 1
    assert not any(row.get("phase") == "Phase 1" and "drug" not in row for row in result.rows)


def test_proportion_operation():
    rows = [
        {"phase": "Phase 1", "trial_count": 1},
        {"phase": "Phase 2", "trial_count": 3},
    ]
    ctx = AggregationContext(
        studies=[],
        plan=ExecutionPlan(metric="proportion", visualization="pie_chart"),
    )
    result = ProportionOperation().apply(ctx, rows, AggregationStep(operation="proportion"))
    assert result[0]["proportion"] == 0.25
    assert result[1]["proportion"] == 0.75


def test_aggregation_service_year(studies):
    service = AggregationService()
    tagged = [TaggedStudy(study=study) for study in studies]
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        group_by="year",
        metric="trial_count",
        visualization="line_chart",
    )

    result = service.aggregate(tagged, plan)

    assert result.group_by == "year"
    assert result.record_count == 4
    assert len(result.rows) == 3


def test_aggregation_service_proportion(studies):
    service = AggregationService()
    tagged = [TaggedStudy(study=study) for study in studies]
    plan = ExecutionPlan(
        group_by="status",
        metric="proportion",
        visualization="pie_chart",
    )

    result = service.aggregate(tagged, plan)

    assert all("proportion" in row for row in result.rows)
    assert round(sum(row["proportion"] for row in result.rows), 4) == 1.0
