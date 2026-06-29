"""Average aggregation operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.operations.base import ENROLLMENT_AVG_FIELD
from app.models.execution_plan import AggregationStep


class AverageOperation:
    """Compute the average of a numeric field across rows."""

    name = "average"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        field = step.field or step.params.get("field", ENROLLMENT_AVG_FIELD)
        values = [row.get(field) for row in rows if row.get(field) is not None]
        if not values:
            return [{field: 0.0}]
        return [{field: round(sum(values) / len(values), 2)}]
