"""Natural language to search intent extraction."""

from app.clients.openai_client import OpenAIClient, OpenAIClientProtocol
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, log_context
from app.models.llm import SearchIntent
from app.models.request import UserQuery
from app.utils.helpers import (
    build_intent_user_message,
    load_prompt,
    merge_explicit_filters,
)

logger = get_logger(__name__)
PROMPT_FILENAME = "query_parser.txt"


class LLMService:
    """Extract structured search intent from natural language queries."""

    def __init__(
        self,
        openai_client: OpenAIClientProtocol,
        *,
        instructions: str | None = None,
    ) -> None:
        self._openai_client = openai_client
        self._instructions = instructions or load_prompt(PROMPT_FILENAME)

    async def extract_search_intent(self, user_query: UserQuery) -> SearchIntent:
        """Parse a user query into a merged, validated search intent."""
        log_context(
            logger,
            "Extracting search intent",
            query=user_query.query,
            explicit_filters=user_query.explicit_filters(),
        )

        user_message = build_intent_user_message(user_query)
        llm_intent, latency_ms = await self._openai_client.parse_search_intent(
            instructions=self._instructions,
            user_message=user_message,
        )
        intent = merge_explicit_filters(llm_intent, user_query)

        log_context(
            logger,
            "Search intent extracted",
            openai_latency_ms=round(latency_ms, 2),
            parsed_intent=intent.model_dump(exclude_none=True),
        )
        return intent


def create_llm_service(settings: Settings | None = None) -> LLMService:
    """Factory for dependency injection."""
    resolved_settings = settings or get_settings()
    return LLMService(openai_client=OpenAIClient(resolved_settings))
