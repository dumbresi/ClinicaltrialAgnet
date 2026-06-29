"""End-to-end query orchestration."""

from app.core.logging import get_logger, log_context
from app.models.request import UserQuery
from app.models.response import VisualizationResponse
from app.services.aggregation_service import AggregationService
from app.services.clinical_trials_service import ClinicalTrialsService
from app.services.llm_service import LLMService
from app.services.visualization_service import VisualizationService

logger = get_logger(__name__)


class QueryService:
    """Orchestrate the full natural-language query pipeline."""

    def __init__(
        self,
        llm_service: LLMService,
        clinical_trials_service: ClinicalTrialsService,
        aggregation_service: AggregationService,
        visualization_service: VisualizationService,
    ) -> None:
        self._llm_service = llm_service
        self._clinical_trials_service = clinical_trials_service
        self._aggregation_service = aggregation_service
        self._visualization_service = visualization_service

    async def process_query(self, user_query: UserQuery) -> VisualizationResponse:
        """Convert a user query into a visualization specification response."""
        log_context(logger, "Processing query", query=user_query.query)

        intent = await self._llm_service.extract_search_intent(user_query)
        search_result = await self._clinical_trials_service.fetch_studies(intent)
        aggregated = self._aggregation_service.aggregate(
            search_result.studies,
            intent,
        )
        response = self._visualization_service.build_response(aggregated, intent)

        log_context(
            logger,
            "Query processed",
            visualization_type=response.visualization.type,
            record_count=response.meta.record_count,
        )
        return response
