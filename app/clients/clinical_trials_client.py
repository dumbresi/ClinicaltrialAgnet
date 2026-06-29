"""Async ClinicalTrials.gov API client."""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

import httpx

from app.core.config import Settings
from app.core.exceptions import (
    ClinicalTrialsAPIError,
    ClinicalTrialsTimeoutError,
)
from app.core.logging import get_logger, log_context
from app.models.clinical_trials import StudiesSearchResult, StudyRecord
from app.services.query_builder import ApiRequestSpec

logger = get_logger(__name__)

STUDIES_PATH = "/studies"
DEFAULT_STUDY_FIELDS = [
    "NCTId",
    "BriefTitle",
    "OverallStatus",
    "StartDate",
    "Phase",
    "LeadSponsorName",
    "LocationCountry",
    "InterventionName",
    "EnrollmentCount",
]


class ClinicalTrialsClientProtocol(Protocol):
    """Protocol for ClinicalTrials.gov client implementations."""

    async def search_with_params(
        self,
        params: dict[str, str | int],
        *,
        page_size: int | None = None,
        max_pages: int | None = None,
    ) -> StudiesSearchResult:
        """Search studies using raw API parameters."""
        ...

    async def execute_request(
        self,
        request: ApiRequestSpec,
        *,
        page_size: int | None = None,
        max_pages: int | None = None,
    ) -> StudiesSearchResult:
        """Execute a single API request spec."""
        ...

    async def get_study(self, nct_id: str) -> StudyRecord:
        """Fetch a single study by NCT ID."""
        ...

    async def aclose(self) -> None:
        """Close the underlying HTTP client if owned by this instance."""
        ...


def build_base_params() -> dict[str, str | int]:
    """Return base API parameters including requested fields."""
    return {
        "format": "json",
        "fields": ",".join(DEFAULT_STUDY_FIELDS),
    }


def parse_study_record(study: dict[str, Any]) -> StudyRecord:
    """Normalize a raw API study payload into a StudyRecord."""
    section = study.get("protocolSection") or {}
    identification = section.get("identificationModule") or {}
    status_module = section.get("statusModule") or {}
    sponsor_module = section.get("sponsorCollaboratorsModule") or {}
    design_module = section.get("designModule") or {}
    locations_module = section.get("contactsLocationsModule") or {}
    interventions_module = section.get("armsInterventionsModule") or {}
    enrollment_module = design_module.get("enrollmentInfo") or {}

    start_date_struct = status_module.get("startDateStruct") or {}
    lead_sponsor = sponsor_module.get("leadSponsor") or {}

    countries = _unique_strings(
        location.get("country")
        for location in locations_module.get("locations") or []
        if location.get("country")
    )
    interventions = _unique_strings(
        intervention.get("name")
        for intervention in interventions_module.get("interventions") or []
        if intervention.get("name")
    )

    enrollment = enrollment_module.get("count")
    if isinstance(enrollment, str) and enrollment.isdigit():
        enrollment = int(enrollment)

    return StudyRecord(
        nct_id=identification.get("nctId", ""),
        brief_title=identification.get("briefTitle"),
        overall_status=status_module.get("overallStatus"),
        start_date=start_date_struct.get("date"),
        phases=list(design_module.get("phases") or []),
        sponsor=lead_sponsor.get("name"),
        countries=countries,
        interventions=interventions,
        enrollment=enrollment if isinstance(enrollment, int) else None,
    )


class ClinicalTrialsClient:
    """Async httpx client for the ClinicalTrials.gov v2 API."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=settings.clinical_trials_base_url_str,
            timeout=settings.timeout_seconds,
            headers={"Accept": "application/json"},
        )

    async def execute_request(
        self,
        request: ApiRequestSpec,
        *,
        page_size: int | None = None,
        max_pages: int | None = None,
    ) -> StudiesSearchResult:
        """Execute a query builder request spec."""
        params = {**build_base_params(), **request.params}
        result = await self.search_with_params(
            params,
            page_size=page_size,
            max_pages=max_pages,
        )
        return result.model_copy(
            update={
                "label": request.label,
                "entity_type": request.entity_type,
                "entity_value": request.entity_value,
            }
        )

    async def search_with_params(
        self,
        params: dict[str, str | int],
        *,
        page_size: int | None = None,
        max_pages: int | None = None,
    ) -> StudiesSearchResult:
        """Search studies with automatic pagination until no nextPageToken."""
        resolved_page_size = page_size or self._settings.clinical_trials_page_size
        resolved_max_pages = (
            max_pages
            if max_pages is not None
            else self._settings.clinical_trials_max_pages
        )
        request_params = dict(params)
        request_params["pageSize"] = resolved_page_size

        log_context(
            logger,
            "ClinicalTrials.gov search started",
            api_params=request_params,
        )

        started = time.perf_counter()
        studies: list[StudyRecord] = []
        pages_fetched = 0
        page_token: str | None = None

        while True:
            if resolved_max_pages is not None and pages_fetched >= resolved_max_pages:
                break

            page_params = dict(request_params)
            if page_token:
                page_params["pageToken"] = page_token

            payload = await self._get_json(STUDIES_PATH, params=page_params)
            pages_fetched += 1

            for raw_study in payload.get("studies") or []:
                record = parse_study_record(raw_study)
                if record.nct_id:
                    studies.append(record)

            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        latency_ms = (time.perf_counter() - started) * 1000
        log_context(
            logger,
            "ClinicalTrials.gov search completed",
            latency_ms=round(latency_ms, 2),
            pages_fetched=pages_fetched,
            study_count=len(studies),
        )

        return StudiesSearchResult(
            studies=studies,
            pages_fetched=pages_fetched,
            api_params=request_params,
            latency_ms=latency_ms,
        )

    async def get_study(self, nct_id: str) -> StudyRecord:
        """Fetch a single study record by NCT ID."""
        normalized_id = nct_id.strip().upper()
        if not normalized_id:
            raise ValueError("nct_id must not be blank")

        log_context(logger, "ClinicalTrials.gov get study started", nct_id=normalized_id)
        started = time.perf_counter()

        payload = await self._get_json(
            f"{STUDIES_PATH}/{normalized_id}",
            params={"format": "json"},
        )
        record = parse_study_record(payload)

        if not record.nct_id:
            raise ClinicalTrialsAPIError(f"Study not found: {normalized_id}")

        latency_ms = (time.perf_counter() - started) * 1000
        log_context(
            logger,
            "ClinicalTrials.gov get study completed",
            nct_id=normalized_id,
            latency_ms=round(latency_ms, 2),
        )
        return record

    async def aclose(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            await self._client.aclose()

    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        """Perform a GET request and return parsed JSON."""
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            log_context(
                logger,
                "ClinicalTrials.gov request timed out",
                level=logging.ERROR,
                path=path,
            )
            raise ClinicalTrialsTimeoutError("ClinicalTrials.gov request timed out") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or exc.response.reason_phrase
            log_context(
                logger,
                "ClinicalTrials.gov API error",
                level=logging.ERROR,
                path=path,
                status_code=exc.response.status_code,
                detail=detail,
            )
            raise ClinicalTrialsAPIError(
                f"ClinicalTrials.gov API error ({exc.response.status_code}): {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            log_context(
                logger,
                "ClinicalTrials.gov transport error",
                level=logging.ERROR,
                path=path,
                error=str(exc),
            )
            raise ClinicalTrialsAPIError("ClinicalTrials.gov request failed") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ClinicalTrialsAPIError("ClinicalTrials.gov returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise ClinicalTrialsAPIError("ClinicalTrials.gov returned unexpected payload")

        return payload


def _unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
