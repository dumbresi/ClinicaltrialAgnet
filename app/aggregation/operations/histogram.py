"""Histogram aggregation operations."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.dimensions import default_histogram_dimension
from app.aggregation.operations.group_by import GroupByOperation
from app.models.execution_plan import AggregationStep


class HistogramOperation:
    """Delegate histogram operations to group_by on a specific dimension."""

    def __init__(self, name: str) -> None:
        self.name = name

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        dimension = default_histogram_dimension(step.operation)
        if dimension is None:
            dimension = step.params.get("dimension", ctx.plan.group_by)
        if not dimension:
            return rows

        group_step = AggregationStep(
            operation="group_by",
            params={"fields": [dimension], "metric": ctx.plan.metric},
        )
        return GroupByOperation().apply(ctx, rows, group_step)


def make_histogram_operation(name: str) -> HistogramOperation:
    """Factory for histogram operation variants."""
    return HistogramOperation(name)
