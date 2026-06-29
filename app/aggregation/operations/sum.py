"""Sum aggregation operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.operations.base import ENROLLMENT_SUM_FIELD
from app.models.execution_plan import AggregationStep


class SumOperation:
    """Sum a numeric field across rows."""

    name = "sum"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        field = step.field or step.params.get("field", ENROLLMENT_SUM_FIELD)
        total = sum(row.get(field, 0) or 0 for row in rows)
        return [{field: total}]
