"""Tests for OpenAI intent extraction."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APITimeoutError

from app.clients.openai_client import OpenAIClient
from app.core.exceptions import InvalidOpenAIResponseError, OpenAITimeoutError
from app.core.config import Settings
from app.models.llm import SearchIntent
from app.models.request import UserQuery
from app.services.llm_service import LLMService
from app.utils.helpers import (
    build_intent_user_message,
    load_prompt,
    merge_explicit_filters,
)


@pytest.fixture
def sample_intent() -> SearchIntent:
    return SearchIntent(
        condition="Breast Cancer",
        metric="trial_count",
        group_by="year",
        visualization_hint="time_series",
        start_year=2018,
        end_year=2025,
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(openai_api_key="test-key")


def test_load_query_parser_prompt():
    prompt = load_prompt("query_parser.txt")
    assert "Do NOT answer medical questions" in prompt
    assert "group_by" in prompt


def test_build_intent_user_message_includes_explicit_filters():
    message = build_intent_user_message(
        UserQuery(
            query="How has the number of trials changed over time?",
            drug_name="Pembrolizumab",
        )
    )
    assert "Pembrolizumab" in message
    assert "explicit_filters" in message


def test_merge_explicit_filters_override_llm(sample_intent):
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
    merged = merge_explicit_filters(sample_intent, user_query)
    assert merged.drug == "Nivolumab"
    assert merged.condition == "Melanoma"
    assert merged.phase == "Phase 3"
    assert merged.sponsor == "NIH"
    assert merged.country == "United States"
    assert merged.start_year == 2020
    assert merged.end_year == 2024
    assert merged.group_by == "year"


@pytest.mark.asyncio
async def test_llm_service_extract_search_intent(sample_intent):
    mock_client = AsyncMock()
    mock_client.parse_search_intent.return_value = (sample_intent, 120.5)

    service = LLMService(openai_client=mock_client, instructions="test instructions")
    user_query = UserQuery(
        query="How has the number of breast cancer trials changed over time?"
    )

    intent = await service.extract_search_intent(user_query)

    assert intent.condition == "Breast Cancer"
    assert intent.group_by == "year"
    mock_client.parse_search_intent.assert_awaited_once()
    call_kwargs = mock_client.parse_search_intent.await_args.kwargs
    assert call_kwargs["instructions"] == "test instructions"
    assert "breast cancer" in call_kwargs["user_message"].lower()


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
        await client.parse_search_intent(
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
        await client.parse_search_intent(
            instructions="test",
            user_message='{"query":"test"}',
        )
