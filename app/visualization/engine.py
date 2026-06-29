"""Visualization engine that selects and builds chart specs."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.exceptions import InvalidVisualizationError
from app.core.logging import get_logger, log_context
from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import MetaData, VisualizationResponse, VisualizationSpec
from app.visualization.registry import VisualizationRegistry, build_default_registry

logger = get_logger(__name__)


class VisualizationEngine:
    """Build visualization specs from execution plans and aggregated data."""

    def __init__(self, registry: VisualizationRegistry | None = None) -> None:
        self._registry = registry or build_default_registry()

    def build_spec(
        self,
        plan: ExecutionPlan,
        aggregated: AggregatedData,
    ) -> VisualizationSpec:
        """Build a visualization specification."""
        if not aggregated.rows:
            raise InvalidVisualizationError("Cannot build visualization from empty data")

        chart_type = self._resolve_chart_type(plan, aggregated)
        builder = self._registry.get(chart_type)

        log_context(
            logger,
            "Building visualization",
            chart_type=chart_type,
            row_count=len(aggregated.rows),
        )

        return builder.build(plan, aggregated)

    def build_response(
        self,
        plan: ExecutionPlan,
        aggregated: AggregatedData,
        *,
        api_calls: int,
        studies_processed: int,
    ) -> VisualizationResponse:
        """Build the full API response including enriched metadata."""
        visualization = self.build_spec(plan, aggregated)
        filters = plan.filters.active_filters()
        if plan.group_by:
            filters["group_by"] = plan.group_by
        filters["metric"] = plan.metric
        if plan.comparison:
            filters["comparison"] = True

        meta = MetaData(
            query_plan=plan.model_dump(exclude_none=True),
            filters=filters,
            api_calls=api_calls,
            studies_processed=studies_processed,
            records_after_filter=aggregated.record_count,
            aggregation=plan.aggregation_label(),
            generated_at=datetime.now(UTC).isoformat(),
            notes=list(aggregated.notes),
        )
        return VisualizationResponse(visualization=visualization, meta=meta)

    def _resolve_chart_type(
        self,
        plan: ExecutionPlan,
        aggregated: AggregatedData,
    ) -> str:
        chart_type = plan.visualization
        if chart_type in self._registry.chart_types:
            return chart_type

        if plan.comparison and plan.group_by:
            return "grouped_bar_chart"
        if plan.group_by == "year":
            return "line_chart"
        if plan.group_by == "country":
            return "map"
        if plan.metric == "proportion":
            return "pie_chart"
        if plan.group_by is None:
            return "kpi"
        return "bar_chart"
