"""Map visualization builder."""

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


class MapBuilder:
    chart_type = "map"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        geo_field = plan.group_by or "country"
        value = value_field(plan)
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                geo=encoding_channel(geo_field, channel_type="nominal"),
                value=encoding_channel(value, label=value_label(plan), channel_type="quantitative"),
            ),
            data=aggregated.rows,
        )
