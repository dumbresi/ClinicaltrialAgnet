"""Natural language to execution plan generation."""

from app.clients.openai_client import OpenAIClientProtocol
from app.core.logging import get_logger, log_context
from app.models.execution_plan import ExecutionPlan
from app.models.request import UserQuery
from app.utils.helpers import (
    build_planner_user_message,
    load_prompt,
    merge_explicit_filters_into_plan,
)

logger = get_logger(__name__)
PROMPT_FILENAME = "query_planner.txt"


class QueryPlannerService:
    """Generate structured execution plans from natural language queries."""

    def __init__(
        self,
        openai_client: OpenAIClientProtocol,
        *,
        instructions: str | None = None,
    ) -> None:
        self._openai_client = openai_client
        self._instructions = instructions or load_prompt(PROMPT_FILENAME)

    async def create_execution_plan(self, user_query: UserQuery) -> ExecutionPlan:
        """Parse a user query into a merged, validated execution plan."""
        log_context(
            logger,
            "Creating execution plan",
            query=user_query.query,
            explicit_filters=user_query.explicit_filters(),
        )

        user_message = build_planner_user_message(user_query)
        plan, latency_ms = await self._openai_client.parse_execution_plan(
            instructions=self._instructions,
            user_message=user_message,
        )
        plan = merge_explicit_filters_into_plan(plan, user_query)

        log_context(
            logger,
            "Execution plan created",
            openai_latency_ms=round(latency_ms, 2),
            intent=plan.intent,
            comparison=plan.comparison,
            entity_count=len(plan.entities),
        )
        return plan
