"""OpenAI Responses API client."""

import logging
import time
from typing import Protocol

from openai import APITimeoutError, AsyncOpenAI
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import InvalidOpenAIResponseError, OpenAITimeoutError
from app.core.logging import get_logger, log_context
from app.models.llm import SearchIntent

logger = get_logger(__name__)


class OpenAIClientProtocol(Protocol):
    """Protocol for OpenAI intent parsing (enables test doubles)."""

    async def parse_search_intent(
        self,
        *,
        instructions: str,
        user_message: str,
    ) -> tuple[SearchIntent, float]:
        """Parse a user message into structured search intent."""
        ...


class OpenAIClient:
    """Async wrapper around the OpenAI Responses API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.timeout_seconds,
        )
        self._model = settings.openai_model

    async def parse_search_intent(
        self,
        *,
        instructions: str,
        user_message: str,
    ) -> tuple[SearchIntent, float]:
        """Call the Responses API and return validated search intent plus latency."""
        started = time.perf_counter()
        log_context(
            logger,
            "OpenAI intent parse request started",
            model=self._model,
        )

        try:
            response = await self._client.responses.parse(
                model=self._model,
                instructions=instructions,
                input=user_message,
                text_format=SearchIntent,
            )
        except APITimeoutError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            log_context(
                logger,
                "OpenAI intent parse timed out",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
            )
            raise OpenAITimeoutError("OpenAI request timed out") from exc
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            log_context(
                logger,
                "OpenAI intent parse failed",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
                error=str(exc),
            )
            raise

        latency_ms = (time.perf_counter() - started) * 1000
        parsed = response.output_parsed

        if parsed is None:
            log_context(
                logger,
                "OpenAI returned no parsed output",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
            )
            raise InvalidOpenAIResponseError("OpenAI returned no structured output")

        try:
            intent = SearchIntent.model_validate(parsed)
        except ValidationError as exc:
            log_context(
                logger,
                "OpenAI parsed output failed validation",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
            )
            raise InvalidOpenAIResponseError(
                "OpenAI returned invalid search intent JSON"
            ) from exc

        log_context(
            logger,
            "OpenAI intent parse completed",
            latency_ms=round(latency_ms, 2),
            group_by=intent.group_by,
            metric=intent.metric,
        )
        return intent, latency_ms
