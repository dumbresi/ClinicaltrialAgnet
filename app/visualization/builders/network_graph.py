"""Network graph visualization builder."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import (
    DIMENSION_LABELS,
    build_title,
    encoding_channel,
    value_field,
    value_label,
)


class NetworkGraphBuilder:
    chart_type = "network_graph"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        value = value_field(plan)
        source_dim = plan.network_source or "source"
        target_dim = plan.network_target or "target"
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                source=encoding_channel(
                    "source",
                    label=DIMENSION_LABELS.get(source_dim, source_dim.title()),
                    channel_type="nominal",
                ),
                target=encoding_channel(
                    "target",
                    label=DIMENSION_LABELS.get(target_dim, target_dim.title()),
                    channel_type="nominal",
                ),
                value=encoding_channel(
                    value,
                    label=value_label(plan),
                    channel_type="quantitative",
                ),
            ),
            data=aggregated.rows,
        )
