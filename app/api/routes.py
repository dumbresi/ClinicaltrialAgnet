"""HTTP route handlers."""

from fastapi import APIRouter, status

from app.api.deps import QueryServiceDep
from app.core.logging import get_logger, log_context
from app.models.request import UserQuery
from app.models.response import VisualizationResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@router.post(
    "/query",
    response_model=VisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert a natural language query into a visualization spec",
)
async def query_clinical_trials(
    user_query: UserQuery,
    query_service: QueryServiceDep,
) -> VisualizationResponse:
    """Process a clinical trial question and return a visualization specification."""
    log_context(
        logger,
        "Incoming query request",
        query=user_query.query,
        explicit_filters=user_query.explicit_filters(),
    )
    return await query_service.process_query(user_query)
