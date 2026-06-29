"""Bar chart visualization builder."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import (
    build_title,
    category_field,
    encoding_channel,
    value_field,
    value_label,
)


class BarChartBuilder:
    chart_type = "bar_chart"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        x_field = category_field(plan, aggregated)
        y_field = value_field(plan)
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                x=encoding_channel(x_field, channel_type="nominal"),
                y=encoding_channel(y_field, label=value_label(plan), channel_type="quantitative"),
            ),
            data=aggregated.rows,
        )
