"""KPI visualization builder."""

from __future__ import annotations

from app.aggregation.operations.base import COUNT_FIELD
from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import build_title, encoding_channel, value_field, value_label


class KpiBuilder:
    chart_type = "kpi"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        value = value_field(plan)
        rows = aggregated.rows
        if rows and value not in rows[0] and COUNT_FIELD in rows[0]:
            value = COUNT_FIELD
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(
                value=encoding_channel(value, label=value_label(plan), channel_type="quantitative"),
            ),
            data=rows,
        )
