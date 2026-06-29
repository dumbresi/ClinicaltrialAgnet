"""ClinicalTrials.gov search orchestration."""

from app.clients.clinical_trials_client import (
    ClinicalTrialsClient,
    ClinicalTrialsClientProtocol,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import NoStudiesFoundError
from app.core.logging import get_logger, log_context
from app.models.clinical_trials import StudiesSearchResult, StudyRecord
from app.models.llm import SearchIntent

logger = get_logger(__name__)


class ClinicalTrialsService:
    """Orchestrate ClinicalTrials.gov searches from structured intent."""

    def __init__(self, client: ClinicalTrialsClientProtocol) -> None:
        self._client = client

    async def fetch_studies(self, intent: SearchIntent) -> StudiesSearchResult:
        """Fetch studies for the given intent, raising when none are found."""
        log_context(
            logger,
            "Fetching studies for intent",
            filters=intent.active_filters(),
            group_by=intent.group_by,
        )

        result = await self._client.search_studies(intent)
        if not result.studies:
            raise NoStudiesFoundError("No studies found for the given search intent")

        log_context(
            logger,
            "Studies fetched",
            study_count=len(result.studies),
            pages_fetched=result.pages_fetched,
            latency_ms=round(result.latency_ms, 2),
        )
        return result

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
