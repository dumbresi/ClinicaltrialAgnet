"""Scatter plot visualization builder."""

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


class ScatterPlotBuilder:
    chart_type = "scatter_plot"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        x_field = plan.group_by or category_field(plan, aggregated)
        y_field = value_field(plan)
        encoding = VisualizationEncoding(
            x=encoding_channel(x_field, channel_type="quantitative"),
            y=encoding_channel(y_field, channel_type="quantitative"),
        )
        if plan.comparison and plan.series_field():
            encoding.series = encoding_channel(plan.series_field(), channel_type="nominal")
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=encoding,
            data=aggregated.rows,
        )
