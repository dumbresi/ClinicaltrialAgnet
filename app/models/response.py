"""API response models."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

VisualizationType = Literal[
    "line_chart",
    "bar_chart",
    "pie_chart",
    "map",
    "network_graph",
]


class EncodingChannel(BaseModel):
    """Mapping from a data field to a visual channel."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., min_length=1, description="Key in each data row.")
    label: str | None = Field(
        default=None,
        description="Human-readable label for the channel.",
    )
    type: Literal["quantitative", "ordinal", "nominal", "temporal"] | None = Field(
        default=None,
        description="Semantic type of the encoded field.",
    )


class VisualizationEncoding(BaseModel):
    """Field-to-channel mapping for a visualization."""

    model_config = ConfigDict(extra="forbid")

    x: EncodingChannel | None = Field(default=None, description="X-axis encoding.")
    y: EncodingChannel | None = Field(default=None, description="Y-axis encoding.")
    series: EncodingChannel | None = Field(
        default=None,
        description="Series or color grouping encoding.",
    )
    source: EncodingChannel | None = Field(
        default=None,
        description="Network graph source node field.",
    )
    target: EncodingChannel | None = Field(
        default=None,
        description="Network graph target node field.",
    )
    value: EncodingChannel | None = Field(
        default=None,
        description="Value encoding for pie charts or edge weights.",
    )
    label: EncodingChannel | None = Field(
        default=None,
        description="Label encoding for categorical charts.",
    )
    geo: EncodingChannel | None = Field(
        default=None,
        description="Geographic region encoding for map charts.",
    )


class VisualizationSpec(BaseModel):
    """Structured visualization specification for frontend rendering."""

    model_config = ConfigDict(extra="forbid")

    type: VisualizationType = Field(..., description="Visualization renderer type.")
    title: str = Field(..., min_length=1, description="Chart title.")
    encoding: VisualizationEncoding = Field(
        ...,
        description="Mapping from data fields to visual channels.",
    )
    data: list[dict[str, Any]] = Field(
        ...,
        description="Tabular data rows used to render the visualization.",
    )


class MetaData(BaseModel):
    """Additional response metadata for rendering and debugging."""

    model_config = ConfigDict(extra="forbid")

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Applied search and aggregation filters.",
    )
    record_count: int = Field(
        ...,
        ge=0,
        description="Number of studies included in the aggregation.",
    )
    source: str = Field(
        default="ClinicalTrials.gov",
        description="Upstream data source.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Assumptions, caveats, or interpretation notes.",
    )


class VisualizationResponse(BaseModel):
    """Top-level API response containing visualization spec and metadata."""

    model_config = ConfigDict(extra="forbid")

    visualization: VisualizationSpec
    meta: MetaData
