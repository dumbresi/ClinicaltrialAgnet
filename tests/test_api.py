"""Tests for FastAPI routes and exception handling."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_query_service
from app.core.exceptions import (
    ClinicalTrialsAPIError,
    ClinicalTrialsTimeoutError,
    InvalidOpenAIResponseError,
    InvalidVisualizationError,
    NoStudiesFoundError,
    OpenAITimeoutError,
)
from app.main import create_app
from app.models.request import UserQuery
from app.models.response import VisualizationResponse
from app.services.query_service import QueryService


@pytest.fixture
def mock_query_service() -> AsyncMock:
    return AsyncMock(spec=QueryService)


@pytest.fixture
def test_client(mock_query_service) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_query_service] = lambda: mock_query_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_success(test_client, mock_query_service):
    mock_query_service.process_query.return_value = VisualizationResponse.model_validate(
        {
            "visualization": {
                "type": "line_chart",
                "title": "Breast Cancer Trials Over Time",
                "encoding": {
                    "x": {"field": "year", "type": "temporal"},
                    "y": {"field": "trial_count", "type": "quantitative"},
                },
                "data": [{"year": 2018, "trial_count": 42}],
            },
            "meta": {
                "query_plan": {"group_by": "year"},
                "filters": {"condition": "Breast Cancer", "group_by": "year"},
                "api_calls": 1,
                "studies_processed": 42,
                "records_after_filter": 42,
                "aggregation": "trial_count_by_year",
                "generated_at": "2026-01-01T00:00:00+00:00",
                "source": "ClinicalTrials.gov",
                "notes": [],
            },
        }
    )

    response = test_client.post(
        "/query",
        json={"query": "How has the number of breast cancer trials changed over time?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["visualization"]["type"] == "line_chart"
    assert body["meta"]["studies_processed"] == 42
    mock_query_service.process_query.assert_awaited_once()


def test_query_validation_error(test_client):
    response = test_client.post("/query", json={"query": ""})
    assert response.status_code == 422


def test_query_no_studies_returns_404(test_client, mock_query_service):
    mock_query_service.process_query.side_effect = NoStudiesFoundError(
        "No studies found for the given search intent"
    )

    response = test_client.post(
        "/query",
        json={"query": "Trials for a nonexistent condition"},
    )

    assert response.status_code == 404
    assert "No studies found" in response.json()["detail"]


def test_query_openai_failure_returns_502(test_client, mock_query_service):
    mock_query_service.process_query.side_effect = InvalidOpenAIResponseError(
        "OpenAI returned invalid search intent JSON"
    )

    response = test_client.post(
        "/query",
        json={"query": "How many breast cancer trials are recruiting?"},
    )

    assert response.status_code == 502


def test_query_clinical_trials_failure_returns_502(test_client, mock_query_service):
    mock_query_service.process_query.side_effect = ClinicalTrialsAPIError(
        "ClinicalTrials.gov API error (500): upstream failure"
    )

    response = test_client.post(
        "/query",
        json={"query": "Breast cancer trials by phase"},
    )

    assert response.status_code == 502


def test_query_openai_timeout_returns_504(test_client, mock_query_service):
    mock_query_service.process_query.side_effect = OpenAITimeoutError(
        "OpenAI request timed out"
    )

    response = test_client.post(
        "/query",
        json={"query": "Breast cancer trials over time"},
    )

    assert response.status_code == 504


def test_query_clinical_trials_timeout_returns_504(test_client, mock_query_service):
    mock_query_service.process_query.side_effect = ClinicalTrialsTimeoutError(
        "ClinicalTrials.gov request timed out"
    )

    response = test_client.post(
        "/query",
        json={"query": "Breast cancer trials over time"},
    )

    assert response.status_code == 504


def test_query_invalid_visualization_returns_400(test_client, mock_query_service):
    mock_query_service.process_query.side_effect = InvalidVisualizationError(
        "Cannot build visualization from empty data"
    )

    response = test_client.post(
        "/query",
        json={"query": "Network graph of trial relationships"},
    )

    assert response.status_code == 400


def test_query_rejects_unknown_fields(test_client):
    response = test_client.post(
        "/query",
        json={
            "query": "Breast cancer trials",
            "unexpected_field": "value",
        },
    )

    assert response.status_code == 422


def test_query_with_explicit_filters(test_client, mock_query_service):
    mock_query_service.process_query.return_value = VisualizationResponse.model_validate(
        {
            "visualization": {
                "type": "bar_chart",
                "title": "Trials for Pembrolizumab by Phase",
                "encoding": {
                    "x": {"field": "phase", "type": "nominal"},
                    "y": {"field": "trial_count", "type": "quantitative"},
                },
                "data": [{"phase": "Phase 2", "trial_count": 10}],
            },
            "meta": {
                "query_plan": {"group_by": "phase"},
                "filters": {"drug": "Pembrolizumab", "group_by": "phase"},
                "api_calls": 1,
                "studies_processed": 10,
                "records_after_filter": 10,
                "aggregation": "trial_count_by_phase",
                "generated_at": "2026-01-01T00:00:00+00:00",
                "source": "ClinicalTrials.gov",
                "notes": [],
            },
        }
    )

    response = test_client.post(
        "/query",
        json={
            "query": "How has the number of trials for this drug changed over time?",
            "drug_name": "Pembrolizumab",
        },
    )

    assert response.status_code == 200
    called_query: UserQuery = mock_query_service.process_query.await_args.args[0]
    assert called_query.drug_name == "Pembrolizumab"
