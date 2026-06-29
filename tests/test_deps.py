"""Tests for dependency injection wiring."""

from app.api.deps import build_app_services
from app.core.config import Settings


def test_build_app_services(settings: Settings):
    services = build_app_services(settings)

    assert services.settings is settings
    assert services.query_planner_service is not None
    assert services.clinical_trials_service is not None
    assert services.aggregation_service is not None
    assert services.visualization_service is not None
    assert services.query_service is not None
