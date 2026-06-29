"""Unique value aggregation operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.models.execution_plan import AggregationStep


class UniqueOperation:
    """Count unique values of a field."""

    name = "unique"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        field = step.field or step.params.get("field", "value")
        unique_values = {row.get(field) for row in rows if row.get(field) is not None}
        return [{field: len(unique_values), "unique_count": len(unique_values)}]
