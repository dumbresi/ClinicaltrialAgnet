"""Aggregation context and tagged study models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.clinical_trials import StudyRecord
from app.models.execution_plan import ExecutionPlan


class TaggedStudy(BaseModel):
    """A study record tagged with an optional comparison series label."""

    model_config = ConfigDict(extra="forbid")

    study: StudyRecord
    series: str | None = Field(
        default=None,
        description="Comparison series label (e.g. drug name).",
    )
    series_field: str | None = Field(
        default=None,
        description="Field name for the series dimension (e.g. 'drug').",
    )


class AggregationContext(BaseModel):
    """Runtime context passed through the aggregation pipeline."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    studies: list[TaggedStudy]
    plan: ExecutionPlan
    notes: list[str] = Field(default_factory=list)

    @property
    def study_count(self) -> int:
        return len(self.studies)
