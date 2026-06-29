"""Pie chart visualization builder."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import (
    build_title,
    category_field,
    encoding_channel,
    value_field,
)


class PieChartBuilder:
    chart_type = "pie_chart"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        label_field = category_field(plan, aggregated)
        value = value_field(plan)
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                label=encoding_channel(label_field, channel_type="nominal"),
                value=encoding_channel(value, channel_type="quantitative"),
            ),
            data=aggregated.rows,
        )
