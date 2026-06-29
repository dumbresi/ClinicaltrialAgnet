"""Tests for configuration and Pydantic models."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.models import ExecutionPlan, UserQuery, VisualizationResponse
from app.models.execution_plan import PlanEntity, PlanFilters


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Ensure each test gets a fresh settings cache."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    settings = Settings()
    assert settings.openai_api_key == "test-key"
    assert settings.clinical_trials_base_url_str == "https://clinicaltrials.gov/api/v2"
    assert settings.timeout_seconds == 30.0
    assert settings.clinical_trials_max_pages is None


def test_user_query_requires_query():
    with pytest.raises(ValidationError):
        UserQuery(query="")


def test_user_query_validates_year_range():
    with pytest.raises(ValidationError):
        UserQuery(query="test query", start_year=2024, end_year=2020)


def test_execution_plan_comparison_requires_two_entities():
    with pytest.raises(ValidationError):
        ExecutionPlan(
            intent="comparison",
            entities=[PlanEntity(type="drug", value="Pembrolizumab")],
            comparison=True,
            visualization="grouped_bar_chart",
        )


def test_execution_plan_filters_active():
    plan = ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer", status="RECRUITING"),
        group_by="year",
        visualization="line_chart",
    )
    assert plan.filters.active_filters()["condition"] == "Breast Cancer"
    assert plan.filters.active_filters()["status"] == "RECRUITING"


def test_visualization_response_shape():
    response = VisualizationResponse.model_validate(
        {
            "visualization": {
                "type": "bar_chart",
                "title": "Trials by Phase for Pembrolizumab",
                "encoding": {
                    "x": {"field": "phase"},
                    "y": {"field": "trial_count"},
                },
                "data": [
                    {"phase": "Phase 1", "trial_count": 32},
                    {"phase": "Phase 2", "trial_count": 78},
                ],
            },
            "meta": {
                "query_plan": {"group_by": "phase"},
                "filters": {"drug": "Pembrolizumab"},
                "api_calls": 1,
                "studies_processed": 110,
                "records_after_filter": 110,
                "aggregation": "trial_count_by_phase",
                "generated_at": "2026-01-01T00:00:00+00:00",
                "source": "ClinicalTrials.gov",
                "notes": [],
            },
        }
    )
    assert response.visualization.type == "bar_chart"
    assert response.meta.studies_processed == 110
