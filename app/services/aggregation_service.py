"""Study data aggregation for visualization."""

from __future__ import annotations

from app.aggregation.context import TaggedStudy
from app.aggregation.engine import AggregationEngine
from app.core.logging import get_logger
from app.models.aggregation import AggregatedData, AggregationOptions
from app.models.execution_plan import ExecutionPlan

logger = get_logger(__name__)


class AggregationService:
    """Aggregate tagged study records into visualization-ready rows."""

    def __init__(self, engine: AggregationEngine | None = None) -> None:
        self._engine = engine or AggregationEngine()

    def aggregate(
        self,
        studies: list[TaggedStudy],
        plan: ExecutionPlan,
        *,
        options: AggregationOptions | None = None,
    ) -> AggregatedData:
        """Aggregate studies according to an execution plan."""
        return self._engine.aggregate(studies, plan, options=options)
