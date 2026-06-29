"""Tests for configuration and Pydantic models."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.models import SearchIntent, UserQuery, VisualizationResponse


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


def test_user_query_requires_query():
    with pytest.raises(ValidationError):
        UserQuery(query="")


def test_user_query_validates_year_range():
    with pytest.raises(ValidationError):
        UserQuery(query="test query", start_year=2024, end_year=2020)


def test_user_query_explicit_filters():
    query = UserQuery(
        query="Trials over time",
        drug_name="Pembrolizumab",
        start_year=2018,
    )
    assert query.explicit_filters() == {
        "drug_name": "Pembrolizumab",
        "start_year": 2018,
    }


def test_search_intent_active_filters():
    intent = SearchIntent(
        condition="Breast Cancer",
        status="RECRUITING",
        metric="trial_count",
        group_by="year",
        visualization_hint="time_series",
    )
    assert intent.active_filters()["condition"] == "Breast Cancer"
    assert intent.active_filters()["status"] == "RECRUITING"


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
                "filters": {"drug_name": "Pembrolizumab"},
                "record_count": 110,
                "source": "ClinicalTrials.gov",
                "notes": [],
            },
        }
    )
    assert response.visualization.type == "bar_chart"
    assert response.meta.record_count == 110
