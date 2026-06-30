"""Visualization type selection and spec generation."""

from __future__ import annotations

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationResponse, VisualizationSpec
from app.visualization.engine import VisualizationEngine


class VisualizationService:
    """Build frontend-ready visualization specs from aggregated data."""

    def __init__(self, engine: VisualizationEngine | None = None) -> None:
        self._engine = engine or VisualizationEngine()

    def build_spec(
        self,
        aggregated: AggregatedData,
        plan: ExecutionPlan,
    ) -> VisualizationSpec:
        """Build a visualization specification from aggregated data."""
        return self._engine.build_spec(plan, aggregated)

    def build_response(
        self,
        aggregated: AggregatedData,
        plan: ExecutionPlan,
        *,
        api_calls: int = 1,
        studies_processed: int = 0,
        plan_notes: list[str] | None = None,
    ) -> VisualizationResponse:
        """Build the full API response including metadata."""
        return self._engine.build_response(
            plan,
            aggregated,
            api_calls=api_calls,
            studies_processed=studies_processed,
            plan_notes=plan_notes,
        )
