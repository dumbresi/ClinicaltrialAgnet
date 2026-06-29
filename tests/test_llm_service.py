"""Tests for OpenAI execution plan extraction."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APITimeoutError

from app.clients.openai_client import OpenAIClient
from app.core.exceptions import InvalidOpenAIResponseError, OpenAITimeoutError
from app.core.config import Settings
from app.models.execution_plan import ExecutionPlan, PlanFilters
from app.models.request import UserQuery
from app.services.query_planner_service import QueryPlannerService
from app.utils.helpers import (
    build_planner_user_message,
    load_prompt,
    merge_explicit_filters_into_plan,
)


@pytest.fixture
def sample_plan() -> ExecutionPlan:
    return ExecutionPlan(
        filters=PlanFilters(condition="Breast Cancer"),
        metric="trial_count",
        group_by="year",
        visualization="line_chart",
        intent="trend",
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(openai_api_key="test-key")


def test_load_query_planner_prompt():
    prompt = load_prompt("query_planner.txt")
    assert "Do NOT answer medical questions" in prompt
    assert "execution plan" in prompt.lower()


def test_build_planner_user_message_includes_explicit_filters():
    message = build_planner_user_message(
        UserQuery(
            query="How has the number of trials changed over time?",
            drug_name="Pembrolizumab",
        )
    )
    assert "Pembrolizumab" in message
    assert "explicit_filters" in message


def test_merge_explicit_filters_into_plan(sample_plan):
    user_query = UserQuery(
        query="Trials over time",
        drug_name="Nivolumab",
        condition="Melanoma",
        trial_phase="Phase 3",
        sponsor="NIH",
        country="United States",
        start_year=2020,
        end_year=2024,
    )
    merged = merge_explicit_filters_into_plan(sample_plan, user_query)
    assert merged.filters.drug == "Nivolumab"
    assert merged.filters.condition == "Melanoma"
    assert merged.filters.phase == "Phase 3"
    assert merged.filters.sponsor == "NIH"
    assert merged.filters.country == "United States"
    assert merged.filters.start_year == 2020
    assert merged.filters.end_year == 2024


@pytest.mark.asyncio
async def test_query_planner_service(sample_plan):
    mock_client = AsyncMock()
    mock_client.parse_execution_plan.return_value = (sample_plan, 120.5)

    service = QueryPlannerService(openai_client=mock_client, instructions="test instructions")
    user_query = UserQuery(
        query="How has the number of breast cancer trials changed over time?"
    )

    plan = await service.create_execution_plan(user_query)

    assert plan.filters.condition == "Breast Cancer"
    assert plan.group_by == "year"
    mock_client.parse_execution_plan.assert_awaited_once()


@pytest.mark.asyncio
async def test_openai_client_raises_on_missing_parsed_output(settings, monkeypatch):
    mock_response = MagicMock()
    mock_response.output_parsed = None

    mock_responses = AsyncMock()
    mock_responses.parse.return_value = mock_response

    mock_async_client = MagicMock()
    mock_async_client.responses = mock_responses
    monkeypatch.setattr(
        "app.clients.openai_client.AsyncOpenAI",
        lambda **kwargs: mock_async_client,
    )

    client = OpenAIClient(settings)

    with pytest.raises(InvalidOpenAIResponseError):
        await client.parse_execution_plan(
            instructions="test",
            user_message='{"query":"test"}',
        )


@pytest.mark.asyncio
async def test_openai_client_maps_timeout(settings, monkeypatch):
    mock_responses = AsyncMock()
    mock_responses.parse.side_effect = APITimeoutError(MagicMock())

    mock_async_client = MagicMock()
    mock_async_client.responses = mock_responses
    monkeypatch.setattr(
        "app.clients.openai_client.AsyncOpenAI",
        lambda **kwargs: mock_async_client,
    )

    client = OpenAIClient(settings)

    with pytest.raises(OpenAITimeoutError):
        await client.parse_execution_plan(
            instructions="test",
            user_message='{"query":"test"}',
        )
