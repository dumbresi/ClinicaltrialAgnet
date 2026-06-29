"""Tests for study aggregation."""

import pytest

from app.models.aggregation import AggregationOptions
from app.models.clinical_trials import StudyRecord
from app.models.llm import SearchIntent
from app.services.aggregation_service import (
    AggregationService,
    apply_metric,
    count_by_country,
    count_by_intervention,
    count_by_phase,
    count_by_sponsor,
    count_by_status,
    count_by_year,
)


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


def test_count_by_year(studies):
    rows = count_by_year(studies)
    assert rows == [
        {"year": 2018, "trial_count": 1},
        {"year": 2019, "trial_count": 1},
        {"year": 2020, "trial_count": 1},
    ]


def test_count_by_phase(studies):
    rows = count_by_phase(studies)
    assert {"phase": "Phase 2", "trial_count": 2} in rows
    assert {"phase": "Phase 3", "trial_count": 2} in rows
    assert {"phase": "Not Specified", "trial_count": 1} in rows


def test_count_by_sponsor(studies):
    rows = count_by_sponsor(studies)
    assert rows[0] == {"sponsor": "Sponsor A", "trial_count": 2}
    assert {"sponsor": "Not Specified", "trial_count": 1} in rows


def test_count_by_country(studies):
    rows = count_by_country(studies)
    assert {"country": "United States", "trial_count": 2} in rows
    assert {"country": "Canada", "trial_count": 1} in rows
    assert {"country": "Not Specified", "trial_count": 1} in rows


def test_count_by_status(studies):
    rows = count_by_status(studies)
    assert {"status": "Recruiting", "trial_count": 2} in rows
    assert {"status": "Completed", "trial_count": 1} in rows


def test_count_by_intervention_top_n(studies):
    rows = count_by_intervention(studies, top_n=2, include_other_bucket=True)
    labels = [row["intervention"] for row in rows]
    assert "Drug A" in labels
    assert "Other" in labels


def test_apply_metric_proportion():
    rows = [
        {"phase": "Phase 1", "trial_count": 1},
        {"phase": "Phase 2", "trial_count": 3},
    ]
    result = apply_metric(rows, "proportion")
    assert result[0]["proportion"] == 0.25
    assert result[1]["proportion"] == 0.75


def test_aggregation_service_year(studies):
    service = AggregationService()
    intent = SearchIntent(
        condition="Breast Cancer",
        group_by="year",
        metric="trial_count",
    )

    result = service.aggregate(studies, intent)

    assert result.group_by == "year"
    assert result.record_count == 4
    assert len(result.rows) == 3
    assert "Excluded 1 studies without a parseable start year." in result.notes


def test_aggregation_service_proportion(studies):
    service = AggregationService()
    intent = SearchIntent(group_by="status", metric="proportion")

    result = service.aggregate(studies, intent)

    assert all("proportion" in row for row in result.rows)
    assert round(sum(row["proportion"] for row in result.rows), 4) == 1.0


def test_aggregation_service_year_range_filter(studies):
    service = AggregationService()
    intent = SearchIntent(
        group_by="year",
        metric="trial_count",
        start_year=2019,
        end_year=2019,
    )

    result = service.aggregate(studies, intent)

    assert result.rows == [{"year": 2019, "trial_count": 1}]
