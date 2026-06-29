"""ClinicalTrials.gov search orchestration."""

from __future__ import annotations

from app.aggregation.context import TaggedStudy
from app.clients.clinical_trials_client import (
    ClinicalTrialsClient,
    ClinicalTrialsClientProtocol,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import NoStudiesFoundError
from app.core.logging import get_logger, log_context
from app.models.clinical_trials import MultiSearchResult, StudyRecord
from app.models.execution_plan import ExecutionPlan
from app.services.query_builder import ApiRequestSpec, QueryBuilder

logger = get_logger(__name__)


class ClinicalTrialsService:
    """Orchestrate ClinicalTrials.gov searches from execution plans."""

    def __init__(
        self,
        client: ClinicalTrialsClientProtocol,
        *,
        query_builder: QueryBuilder | None = None,
    ) -> None:
        self._client = client
        self._query_builder = query_builder or QueryBuilder()

    async def fetch_studies(self, plan: ExecutionPlan) -> MultiSearchResult:
        """Fetch studies for the given plan, supporting multiple API requests."""
        build_result = self._query_builder.build(plan)
        log_context(
            logger,
            "Fetching studies for execution plan",
            api_requests=len(build_result.requests),
            filters=plan.filters.active_filters(),
        )

        results = []
        total_studies = 0
        total_latency = 0.0

        for request in build_result.requests:
            result = await self._client.execute_request(request)
            results.append(result)
            total_studies += len(result.studies)
            total_latency += result.latency_ms

        if total_studies == 0:
            raise NoStudiesFoundError("No studies found for the given execution plan")

        log_context(
            logger,
            "Studies fetched",
            api_calls=len(results),
            studies_processed=total_studies,
            latency_ms=round(total_latency, 2),
        )

        return MultiSearchResult(
            results=results,
            api_calls=len(results),
            studies_processed=total_studies,
            total_latency_ms=total_latency,
        )

    def tag_studies(
        self,
        search_result: MultiSearchResult,
        plan: ExecutionPlan,
    ) -> list[TaggedStudy]:
        """Convert multi-search results into tagged studies for aggregation."""
        tagged: list[TaggedStudy] = []
        series_field = plan.series_field()

        for result in search_result.results:
            label = result.label or "all"
            for study in result.studies:
                tagged.append(
                    TaggedStudy(
                        study=study,
                        series=label if plan.comparison or result.label else None,
                        series_field=series_field,
                    )
                )
        return tagged

    async def get_study(self, nct_id: str) -> StudyRecord:
        """Fetch a single study by NCT ID."""
        return await self._client.get_study(nct_id)


def create_clinical_trials_service(
    settings: Settings | None = None,
    *,
    client: ClinicalTrialsClientProtocol | None = None,
) -> ClinicalTrialsService:
    """Factory for dependency injection."""
    resolved_settings = settings or get_settings()
    resolved_client = client or ClinicalTrialsClient(resolved_settings)
    return ClinicalTrialsService(resolved_client)
