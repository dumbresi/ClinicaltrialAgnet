"""Grouped bar chart visualization builder."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import (
    build_title,
    encoding_channel,
    value_field,
    value_label,
)


class GroupedBarChartBuilder:
    chart_type = "grouped_bar_chart"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        series_field = plan.series_field() or "series"
        group_field = plan.group_by or "category"
        y_field = value_field(plan)
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                x=encoding_channel(group_field, channel_type="nominal"),
                y=encoding_channel(y_field, label=value_label(plan), channel_type="quantitative"),
                series=encoding_channel(series_field, channel_type="nominal"),
            ),
            data=aggregated.rows,
        )
