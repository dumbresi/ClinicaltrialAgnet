"""Shared pytest fixtures."""

import pytest

from app.core.config import Settings, get_settings
from app.models.clinical_trials import StudyRecord


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Ensure each test gets a fresh settings cache."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings(monkeypatch) -> Settings:
    """Default test settings with a dummy OpenAI key."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return Settings(openai_api_key="test-key")


@pytest.fixture
def sample_studies() -> list[StudyRecord]:
    """Representative study records for pipeline tests."""
    return [
        StudyRecord(
            nct_id="NCT00000001",
            overall_status="RECRUITING",
            start_date="2018-03-01",
            phases=["PHASE2"],
            sponsor="Sponsor A",
            countries=["United States"],
            interventions=["Pembrolizumab"],
        ),
        StudyRecord(
            nct_id="NCT00000002",
            overall_status="COMPLETED",
            start_date="2019-07-15",
            phases=["PHASE2"],
            sponsor="Sponsor B",
            countries=["United States"],
            interventions=["Pembrolizumab"],
        ),
        StudyRecord(
            nct_id="NCT00000003",
            overall_status="RECRUITING",
            start_date="2020-01-01",
            phases=["PHASE3"],
            sponsor="Sponsor A",
            countries=["France"],
            interventions=["Drug B"],
        ),
    ]
