"""LLM structured output models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Metric = Literal["trial_count", "proportion"]
GroupBy = Literal[
    "year",
    "phase",
    "sponsor",
    "country",
    "status",
    "intervention",
]
VisualizationHint = Literal[
    "time_series",
    "bar_chart",
    "pie_chart",
    "map",
    "network_graph",
]
StudyStatus = Literal[
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "COMPLETED",
    "ENROLLING_BY_INVITATION",
    "SUSPENDED",
    "TERMINATED",
    "WITHDRAWN",
    "UNKNOWN",
]


class SearchIntent(BaseModel):
    """Structured search intent extracted from a natural language query.

    The LLM must only populate search and aggregation parameters. It must not
    answer medical questions or return narrative responses.
    """

    model_config = ConfigDict(extra="forbid")

    condition: str | None = Field(
        default=None,
        description="Disease or condition to filter studies by.",
    )
    drug: str | None = Field(
        default=None,
        description="Drug or intervention name to filter studies by.",
    )
    phase: str | None = Field(
        default=None,
        description="Trial phase filter, e.g. 'Phase 2'.",
    )
    sponsor: str | None = Field(
        default=None,
        description="Sponsor or organization name to filter studies by.",
    )
    status: StudyStatus | None = Field(
        default=None,
        description="Recruitment or overall study status filter.",
    )
    country: str | None = Field(
        default=None,
        description="Country or location filter.",
    )
    start_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Inclusive lower bound on study start year.",
    )
    end_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Inclusive upper bound on study start year.",
    )
    metric: Metric = Field(
        default="trial_count",
        description="Metric to compute for visualization.",
    )
    group_by: GroupBy = Field(
        default="year",
        description="Dimension used to aggregate study results.",
    )
    visualization_hint: VisualizationHint = Field(
        default="time_series",
        description="Suggested visualization type based on the query intent.",
    )

    @field_validator("condition", "drug", "phase", "sponsor", "country", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object:
        """Normalize blank strings to null."""
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def validate_year_range(self) -> "SearchIntent":
        """Ensure end_year is not before start_year when both are provided."""
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.end_year < self.start_year
        ):
            raise ValueError("end_year must be greater than or equal to start_year")
        return self

    def active_filters(self) -> dict[str, str | int]:
        """Return non-null search filters for response metadata."""
        filters: dict[str, str | int] = {}
        if self.condition is not None:
            filters["condition"] = self.condition
        if self.drug is not None:
            filters["drug"] = self.drug
        if self.phase is not None:
            filters["phase"] = self.phase
        if self.sponsor is not None:
            filters["sponsor"] = self.sponsor
        if self.status is not None:
            filters["status"] = self.status
        if self.country is not None:
            filters["country"] = self.country
        if self.start_year is not None:
            filters["start_year"] = self.start_year
        if self.end_year is not None:
            filters["end_year"] = self.end_year
        return filters
