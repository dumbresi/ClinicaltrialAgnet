"""Network graph visualization builder."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import build_title, encoding_channel, value_field


class NetworkGraphBuilder:
    chart_type = "network_graph"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        value = value_field(plan)
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                source=encoding_channel("source", channel_type="nominal"),
                target=encoding_channel("target", channel_type="nominal"),
                value=encoding_channel(value, channel_type="quantitative"),
            ),
            data=aggregated.rows,
        )
