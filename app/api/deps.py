"""FastAPI dependency injection."""

from dataclasses import dataclass
from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.clients.clinical_trials_client import ClinicalTrialsClient
from app.clients.openai_client import OpenAIClient
from app.core.config import Settings, get_settings
from app.services.aggregation_service import AggregationService
from app.services.clinical_trials_service import ClinicalTrialsService
from app.services.query_planner_service import QueryPlannerService
from app.services.query_service import QueryService
from app.services.visualization_service import VisualizationService
from app.utils.helpers import load_prompt


@dataclass
class AppServices:
    """Container for application services wired at startup."""

    settings: Settings
    http_client: httpx.AsyncClient
    openai_client: OpenAIClient
    clinical_trials_client: ClinicalTrialsClient
    query_planner_service: QueryPlannerService
    clinical_trials_service: ClinicalTrialsService
    aggregation_service: AggregationService
    visualization_service: VisualizationService
    query_service: QueryService


def build_app_services(settings: Settings) -> AppServices:
    """Construct the service graph for the application."""
    http_client = httpx.AsyncClient(
        base_url=settings.clinical_trials_base_url_str,
        timeout=settings.timeout_seconds,
        headers={"Accept": "application/json"},
    )
    openai_client = OpenAIClient(settings)
    clinical_trials_client = ClinicalTrialsClient(
        settings,
        http_client=http_client,
    )
    query_planner_service = QueryPlannerService(
        openai_client=openai_client,
        instructions=load_prompt("query_planner.txt"),
    )
    clinical_trials_service = ClinicalTrialsService(clinical_trials_client)
    aggregation_service = AggregationService()
    visualization_service = VisualizationService()
    query_service = QueryService(
        query_planner_service=query_planner_service,
        clinical_trials_service=clinical_trials_service,
        aggregation_service=aggregation_service,
        visualization_service=visualization_service,
    )

    return AppServices(
        settings=settings,
        http_client=http_client,
        openai_client=openai_client,
        clinical_trials_client=clinical_trials_client,
        query_planner_service=query_planner_service,
        clinical_trials_service=clinical_trials_service,
        aggregation_service=aggregation_service,
        visualization_service=visualization_service,
        query_service=query_service,
    )


async def shutdown_app_services(services: AppServices) -> None:
    """Release resources held by application services."""
    await services.http_client.aclose()
    await services.clinical_trials_client.aclose()


def get_app_services(request: Request) -> AppServices:
    """Return services attached to application state."""
    return request.app.state.services


def get_query_service(
    services: Annotated[AppServices, Depends(get_app_services)],
) -> QueryService:
    """Return the query orchestration service."""
    return services.query_service


SettingsDep = Annotated[Settings, Depends(get_settings)]
QueryServiceDep = Annotated[QueryService, Depends(get_query_service)]
