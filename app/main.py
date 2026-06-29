"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.deps import build_app_services, shutdown_app_services
from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    ClinicalTrialsAPIError,
    ClinicalTrialsTimeoutError,
    InvalidOpenAIResponseError,
    InvalidVisualizationError,
    NoStudiesFoundError,
    OpenAIServiceError,
    OpenAITimeoutError,
)
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down application resources."""
    settings = get_settings()
    setup_logging(settings)
    services = build_app_services(settings)
    app.state.services = services
    log_startup(settings)
    yield
    await shutdown_app_services(services)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Clinical Trial Visualization API",
        description=(
            "Convert natural language clinical trial questions into structured "
            "visualization specifications backed by ClinicalTrials.gov data."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    register_exception_handlers(app)
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to HTTP responses."""

    @app.exception_handler(NoStudiesFoundError)
    async def no_studies_handler(
        request: Request,
        exc: NoStudiesFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidVisualizationError)
    async def invalid_visualization_handler(
        request: Request,
        exc: InvalidVisualizationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidOpenAIResponseError)
    async def invalid_openai_handler(
        request: Request,
        exc: InvalidOpenAIResponseError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(OpenAITimeoutError)
    async def openai_timeout_handler(
        request: Request,
        exc: OpenAITimeoutError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(OpenAIServiceError)
    async def openai_service_handler(
        request: Request,
        exc: OpenAIServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": "OpenAI intent extraction failed"},
        )

    @app.exception_handler(ClinicalTrialsTimeoutError)
    async def clinical_trials_timeout_handler(
        request: Request,
        exc: ClinicalTrialsTimeoutError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ClinicalTrialsAPIError)
    async def clinical_trials_api_handler(
        request: Request,
        exc: ClinicalTrialsAPIError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected application error occurred"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )


def log_startup(settings) -> None:
    """Log key configuration at startup."""
    logger.info(
        "Application started | clinical_trials_base_url=%r timeout_seconds=%r openai_model=%r",
        settings.clinical_trials_base_url_str,
        settings.timeout_seconds,
        settings.openai_model,
    )


app = create_app()
