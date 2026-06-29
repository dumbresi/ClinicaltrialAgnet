"""Execution plan models produced by the LLM query planner."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.llm import StudyStatus

QueryIntent = Literal[
    "single",
    "comparison",
    "distribution",
    "trend",
    "relationship",
    "summary",
]

EntityType = Literal[
    "drug",
    "condition",
    "sponsor",
    "country",
    "phase",
    "status",
    "intervention_type",
    "study_type",
]

PlanMetric = Literal[
    "trial_count",
    "proportion",
    "enrollment_sum",
    "enrollment_average",
]

GroupByDimension = Literal[
    "year",
    "phase",
    "sponsor",
    "country",
    "status",
    "intervention",
    "enrollment",
]

PlanVisualization = Literal[
    "line_chart",
    "bar_chart",
    "grouped_bar_chart",
    "stacked_bar_chart",
    "pie_chart",
    "scatter_plot",
    "table",
    "map",
    "network_graph",
    "kpi",
]

AggregationOperationName = Literal[
    "count",
    "group_by",
    "sum",
    "average",
    "median",
    "unique",
    "top_n",
    "sort",
    "proportion",
    "date_histogram",
    "country_histogram",
    "phase_histogram",
    "status_histogram",
    "sponsor_histogram",
    "network_edges",
]


class PlanEntity(BaseModel):
    """An entity involved in the query, typically for comparisons."""

    model_config = ConfigDict(extra="forbid")

    type: EntityType = Field(..., description="Entity category.")
    value: str = Field(..., min_length=1, description="Entity value.")
    label: str | None = Field(
        default=None,
        description="Optional display label; defaults to value.",
    )

    @field_validator("value", "label", mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @property
    def display_label(self) -> str:
        """Return the label used in aggregated rows and chart series."""
        return self.label or self.value


class PlanFilters(BaseModel):
    """Shared filters applied to every API request in the plan."""

    model_config = ConfigDict(extra="forbid")

    condition: str | None = None
    drug: str | None = None
    phase: str | None = None
    sponsor: str | None = None
    status: StudyStatus | None = None
    country: str | None = None
    intervention_type: str | None = None
    study_type: str | None = None
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)
    min_enrollment: int | None = Field(default=None, ge=0)
    max_enrollment: int | None = Field(default=None, ge=0)

    @field_validator(
        "condition",
        "drug",
        "phase",
        "sponsor",
        "country",
        "intervention_type",
        "study_type",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def validate_year_range(self) -> "PlanFilters":
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.end_year < self.start_year
        ):
            raise ValueError("end_year must be greater than or equal to start_year")
        return self

    def active_filters(self) -> dict[str, Any]:
        """Return non-null filters for response metadata."""
        filters: dict[str, Any] = {}
        for field_name in PlanFilters.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                filters[field_name] = value
        return filters


class AggregationStep(BaseModel):
    """A single step in the aggregation pipeline."""

    model_config = ConfigDict(extra="forbid")

    operation: AggregationOperationName
    field: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Structured execution plan produced by the LLM query planner.

    The planner describes WHAT to analyze, not HOW to call the API.
    Downstream services translate this plan into API requests, aggregations,
    and visualizations.
    """

    model_config = ConfigDict(extra="forbid")

    intent: QueryIntent = Field(
        default="single",
        description="High-level query intent.",
    )
    entities: list[PlanEntity] = Field(
        default_factory=list,
        description="Entities to compare or highlight.",
    )
    filters: PlanFilters = Field(
        default_factory=PlanFilters,
        description="Shared filters for all API requests.",
    )
    metric: PlanMetric = Field(
        default="trial_count",
        description="Primary metric to compute.",
    )
    group_by: GroupByDimension | None = Field(
        default=None,
        description="Primary grouping dimension.",
    )
    visualization: PlanVisualization = Field(
        default="bar_chart",
        description="Requested visualization type.",
    )
    comparison: bool = Field(
        default=False,
        description="Whether entities should be compared as separate series.",
    )
    network_source: str | None = Field(
        default=None,
        description="Source node field for network_graph visualizations.",
    )
    network_target: str | None = Field(
        default=None,
        description="Target node field for network_graph visualizations.",
    )

    @model_validator(mode="after")
    def validate_comparison_entities(self) -> "ExecutionPlan":
        if self.comparison and len(self.entities) < 2:
            raise ValueError("comparison=true requires at least two entities")
        if self.comparison and self.entities:
            entity_types = {entity.type for entity in self.entities}
            if len(entity_types) > 1:
                raise ValueError("comparison entities must share the same type")
        return self

    def series_field(self) -> str | None:
        """Return the data field used for comparison series, if any."""
        if not self.comparison or not self.entities:
            return None
        return self.entities[0].type

    def aggregation_label(self) -> str:
        """Human-readable aggregation identifier for metadata."""
        parts = [self.metric]
        if self.comparison and self.series_field():
            parts.append(f"by_{self.series_field()}")
        if self.group_by:
            parts.append(f"by_{self.group_by}")
        return "_".join(parts)
