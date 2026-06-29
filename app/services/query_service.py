"""End-to-end query orchestration."""

from app.core.logging import get_logger, log_context
from app.models.request import UserQuery
from app.models.response import VisualizationResponse
from app.services.aggregation_service import AggregationService
from app.services.clinical_trials_service import ClinicalTrialsService
from app.services.query_planner_service import QueryPlannerService
from app.services.visualization_service import VisualizationService

logger = get_logger(__name__)


class QueryService:
    """Orchestrate the full natural-language query pipeline."""

    def __init__(
        self,
        query_planner_service: QueryPlannerService,
        clinical_trials_service: ClinicalTrialsService,
        aggregation_service: AggregationService,
        visualization_service: VisualizationService,
    ) -> None:
        self._query_planner_service = query_planner_service
        self._clinical_trials_service = clinical_trials_service
        self._aggregation_service = aggregation_service
        self._visualization_service = visualization_service

    async def process_query(self, user_query: UserQuery) -> VisualizationResponse:
        """Convert a user query into a visualization specification response."""
        log_context(logger, "Processing query", query=user_query.query)

        plan = await self._query_planner_service.create_execution_plan(user_query)
        search_result = await self._clinical_trials_service.fetch_studies(plan)
        tagged_studies = self._clinical_trials_service.tag_studies(search_result, plan)
        aggregated = self._aggregation_service.aggregate(tagged_studies, plan)
        response = self._visualization_service.build_response(
            aggregated,
            plan,
            api_calls=search_result.api_calls,
            studies_processed=search_result.studies_processed,
        )

        log_context(
            logger,
            "Query processed",
            visualization_type=response.visualization.type,
            api_calls=response.meta.api_calls,
            studies_processed=response.meta.studies_processed,
        )
        return response
