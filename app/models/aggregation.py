"""Aggregated study data models."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Metric = Literal["trial_count", "proportion", "enrollment_sum", "enrollment_average"]


class AggregatedData(BaseModel):
    """Tabular aggregation output consumed by the visualization layer."""

    model_config = ConfigDict(extra="forbid")

    group_by: str = Field(..., description="Dimension(s) used for aggregation.")
    metric: Metric = Field(..., description="Metric applied to grouped rows.")
    rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Aggregated data rows.",
    )
    record_count: int = Field(
        ...,
        ge=0,
        description="Number of input studies aggregated.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Aggregation assumptions or caveats.",
    )
    series_field: str | None = Field(
        default=None,
        description="Comparison series field when comparison=true.",
    )
    comparison: bool = Field(
        default=False,
        description="Whether rows include comparison series.",
    )


class AggregationOptions(BaseModel):
    """Optional aggregation tuning parameters."""

    model_config = ConfigDict(extra="forbid")

    top_n: int = Field(default=20, ge=1, le=100)
    include_other_bucket: bool = Field(default=True)
