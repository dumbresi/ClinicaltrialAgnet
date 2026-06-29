"""Aggregated study data models."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.llm import GroupBy, Metric


class AggregatedData(BaseModel):
    """Tabular aggregation output consumed by the visualization layer."""

    model_config = ConfigDict(extra="forbid")

    group_by: GroupBy = Field(..., description="Dimension used for aggregation.")
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


class AggregationOptions(BaseModel):
    """Optional aggregation tuning parameters."""

    model_config = ConfigDict(extra="forbid")

    top_n: int = Field(default=20, ge=1, le=100)
    include_other_bucket: bool = Field(default=True)
