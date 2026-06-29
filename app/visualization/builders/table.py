"""Table visualization builder."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationEncoding, VisualizationSpec
from app.visualization.builders.base import build_title


class TableBuilder:
    chart_type = "table"

    def build(self, plan: ExecutionPlan, aggregated: AggregatedData) -> VisualizationSpec:
        return VisualizationSpec(
            type=self.chart_type,
            title=build_title(plan),
            encoding=VisualizationEncoding(),
            data=aggregated.rows,
        )
