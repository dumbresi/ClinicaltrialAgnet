"""ClinicalTrials.gov API data models."""

from pydantic import BaseModel, ConfigDict, Field


class StudyRecord(BaseModel):
    """Normalized study fields used by aggregation and visualization."""

    model_config = ConfigDict(extra="forbid")

    nct_id: str = Field(..., min_length=1, description="ClinicalTrials.gov NCT identifier.")
    brief_title: str | None = Field(default=None, description="Short study title.")
    overall_status: str | None = Field(default=None, description="Overall recruitment status.")
    start_date: str | None = Field(
        default=None,
        description="Study start date (YYYY-MM-DD or YYYY-MM).",
    )
    phases: list[str] = Field(default_factory=list, description="Study phases.")
    sponsor: str | None = Field(default=None, description="Lead sponsor name.")
    countries: list[str] = Field(default_factory=list, description="Location countries.")
    interventions: list[str] = Field(
        default_factory=list,
        description="Intervention names associated with the study.",
    )
    enrollment: int | None = Field(
        default=None,
        description="Target or actual enrollment count.",
    )


class StudiesSearchResult(BaseModel):
    """Paginated ClinicalTrials.gov search result."""

    model_config = ConfigDict(extra="forbid")

    studies: list[StudyRecord] = Field(default_factory=list)
    pages_fetched: int = Field(..., ge=0)
    api_params: dict[str, str | int] = Field(default_factory=dict)
    latency_ms: float = Field(..., ge=0)
    label: str | None = Field(
        default=None,
        description="Series label when part of a multi-request fetch.",
    )
    entity_type: str | None = None
    entity_value: str | None = None


class MultiSearchResult(BaseModel):
    """Combined result from multiple API requests."""

    model_config = ConfigDict(extra="forbid")

    results: list[StudiesSearchResult] = Field(default_factory=list)
    api_calls: int = Field(..., ge=0)
    studies_processed: int = Field(..., ge=0)
    total_latency_ms: float = Field(..., ge=0)
