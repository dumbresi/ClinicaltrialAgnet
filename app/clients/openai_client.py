"""OpenAI Responses API client."""

import logging
import time
from typing import Protocol

from openai import APITimeoutError, AsyncOpenAI, BadRequestError
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import InvalidOpenAIResponseError, OpenAITimeoutError
from app.core.logging import get_logger, log_context
from app.models.execution_plan import ExecutionPlan

logger = get_logger(__name__)


class OpenAIClientProtocol(Protocol):
    """Protocol for OpenAI execution plan parsing (enables test doubles)."""

    async def parse_execution_plan(
        self,
        *,
        instructions: str,
        user_message: str,
    ) -> tuple[ExecutionPlan, float]:
        """Parse a user message into a structured execution plan."""
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

    async def parse_execution_plan(
        self,
        *,
        instructions: str,
        user_message: str,
    ) -> tuple[ExecutionPlan, float]:
        """Call the Responses API and return a validated execution plan plus latency."""
        started = time.perf_counter()
        log_context(
            logger,
            "OpenAI execution plan request started",
            model=self._model,
        )

        try:
            response = await self._client.responses.parse(
                model=self._model,
                instructions=instructions,
                input=user_message,
                text_format=ExecutionPlan,
            )
        except APITimeoutError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            log_context(
                logger,
                "OpenAI execution plan request timed out",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
            )
            raise OpenAITimeoutError("OpenAI request timed out") from exc
        except BadRequestError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            log_context(
                logger,
                "OpenAI execution plan request rejected",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
                error=str(exc),
            )
            raise InvalidOpenAIResponseError(
                "OpenAI rejected the execution plan schema or request"
            ) from exc
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            log_context(
                logger,
                "OpenAI execution plan request failed",
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
            plan = ExecutionPlan.model_validate(parsed)
        except ValidationError as exc:
            log_context(
                logger,
                "OpenAI parsed output failed validation",
                level=logging.ERROR,
                latency_ms=round(latency_ms, 2),
            )
            raise InvalidOpenAIResponseError(
                "OpenAI returned invalid execution plan JSON"
            ) from exc

        log_context(
            logger,
            "OpenAI execution plan completed",
            latency_ms=round(latency_ms, 2),
            intent=plan.intent,
            group_by=plan.group_by,
        )
        return plan, latency_ms
