"""Median aggregation operation."""

from __future__ import annotations

from statistics import median
from typing import Any

from app.aggregation.context import AggregationContext
from app.models.execution_plan import AggregationStep


class MedianOperation:
    """Compute the median of a numeric field across rows."""

    name = "median"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        field = step.field or step.params.get("field", "value")
        values = sorted(row.get(field, 0) or 0 for row in rows)
        if not values:
            return [{field: 0.0}]
        return [{field: float(median(values))}]
