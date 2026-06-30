"""Translate execution plans into ClinicalTrials.gov API request specifications."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.exceptions import InvalidExecutionPlanError
from app.models.execution_plan import EntityType, ExecutionPlan, PlanEntity, PlanFilters
from app.utils.helpers import normalize_phase_token

ENTITY_QUERY_PARAM: dict[EntityType, str] = {
    "drug": "query.intr",
    "condition": "query.cond",
    "sponsor": "query.spons",
    "country": "query.locn",
}

COMPARABLE_ENTITY_TYPES: frozenset[EntityType] = frozenset(
    {"drug", "condition", "sponsor", "country", "phase", "status"}
)


class ApiRequestSpec(BaseModel):
    """A single ClinicalTrials.gov API search request."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., description="Series label for aggregated results.")
    entity_type: EntityType | None = Field(
        default=None,
        description="Entity type when this request represents a comparison arm.",
    )
    entity_value: str | None = Field(
        default=None,
        description="Entity value when this request represents a comparison arm.",
    )
    params: dict[str, str | int] = Field(
        default_factory=dict,
        description="ClinicalTrials.gov v2 query parameters.",
    )


class QueryBuildResult(BaseModel):
    """Output of the query builder."""

    model_config = ConfigDict(extra="forbid")

    requests: list[ApiRequestSpec] = Field(default_factory=list)


class QueryBuilder:
    """Build one or more ClinicalTrials.gov API requests from an execution plan."""

    def build(self, plan: ExecutionPlan) -> QueryBuildResult:
        """Return API request specs for the given execution plan."""
        if plan.comparison and len(plan.entities) >= 2:
            requests = [
                self._build_entity_request(plan.filters, entity)
                for entity in plan.entities
            ]
            return QueryBuildResult(requests=requests)

        params = self._build_params(plan.filters)
        for entity in plan.entities:
            self._apply_entity(params, entity)

        if not _has_search_criteria(params):
            if plan.allows_unscoped_search():
                params["query.term"] = "clinical trial"
            else:
                raise InvalidExecutionPlanError(
                    "Could not identify clinical trial search criteria in the execution plan."
                )

        label = plan.entities[0].display_label if plan.entities else "all"
        return QueryBuildResult(
            requests=[
                ApiRequestSpec(
                    label=label,
                    entity_type=plan.entities[0].type if plan.entities else None,
                    entity_value=plan.entities[0].value if plan.entities else None,
                    params=params,
                )
            ]
        )

    def _build_entity_request(
        self,
        filters: PlanFilters,
        entity: PlanEntity,
    ) -> ApiRequestSpec:
        params = self._build_params(filters)
        self._apply_entity(params, entity)
        if not _has_search_criteria(params):
            if plan.allows_unscoped_search():
                params["query.term"] = "clinical trial"
            else:
                raise InvalidExecutionPlanError(
                    "Could not identify clinical trial search criteria in the execution plan."
                )
        return ApiRequestSpec(
            label=entity.display_label,
            entity_type=entity.type,
            entity_value=entity.value,
            params=params,
        )

    def _build_params(self, filters: PlanFilters) -> dict[str, str | int]:
        params: dict[str, str | int] = {}

        if filters.condition:
            params["query.cond"] = filters.condition
        if filters.drug:
            params["query.intr"] = filters.drug
        if filters.sponsor:
            params["query.spons"] = filters.sponsor
        if filters.country:
            params["query.locn"] = filters.country
        if filters.status:
            params["filter.overallStatus"] = filters.status

        advanced_filters: list[str] = []

        if filters.phase:
            phase_token = normalize_phase_token(filters.phase)
            if phase_token:
                advanced_filters.append(f"AREA[Phase]{phase_token}")

        if filters.intervention_type:
            advanced_filters.append(f"AREA[InterventionType]{filters.intervention_type}")

        if filters.study_type:
            advanced_filters.append(f"AREA[StudyType]{filters.study_type}")

        if filters.start_year is not None or filters.end_year is not None:
            start = f"{filters.start_year:04d}-01-01" if filters.start_year else "MIN"
            end = f"{filters.end_year:04d}-12-31" if filters.end_year else "MAX"
            advanced_filters.append(f"AREA[StartDate]RANGE[{start},{end}]")

        if filters.min_enrollment is not None or filters.max_enrollment is not None:
            low = str(filters.min_enrollment) if filters.min_enrollment is not None else "MIN"
            high = str(filters.max_enrollment) if filters.max_enrollment is not None else "MAX"
            advanced_filters.append(f"AREA[EnrollmentCount]RANGE[{low},{high}]")

        if advanced_filters:
            params["filter.advanced"] = " AND ".join(advanced_filters)

        return params

    def _apply_entity(
        self,
        params: dict[str, str | int],
        entity: PlanEntity,
    ) -> None:
        if entity.type in ENTITY_QUERY_PARAM:
            params[ENTITY_QUERY_PARAM[entity.type]] = entity.value
            return

        if entity.type == "phase":
            phase_token = normalize_phase_token(entity.value)
            if phase_token:
                _append_advanced(params, f"AREA[Phase]{phase_token}")
            return

        if entity.type == "status":
            params["filter.overallStatus"] = entity.value
            return

        if entity.type == "intervention_type":
            _append_advanced(params, f"AREA[InterventionType]{entity.value}")
            return

        if entity.type == "study_type":
            _append_advanced(params, f"AREA[StudyType]{entity.value}")


def _append_advanced(params: dict[str, str | int], clause: str) -> None:
    existing = params.get("filter.advanced")
    if existing:
        params["filter.advanced"] = f"{existing} AND {clause}"
    else:
        params["filter.advanced"] = clause


def _has_search_criteria(params: dict[str, str | int]) -> bool:
    query_keys = (
        "query.cond",
        "query.intr",
        "query.spons",
        "query.locn",
        "query.term",
        "filter.overallStatus",
        "filter.advanced",
    )
    return any(key in params for key in query_keys)
