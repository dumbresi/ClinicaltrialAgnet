"""Sort aggregation operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.operations.base import COUNT_FIELD
from app.models.execution_plan import AggregationStep


class SortOperation:
    """Sort aggregated rows by a field."""

    name = "sort"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        field = step.field or step.params.get("field", COUNT_FIELD)
        descending = step.params.get("descending", False)
        return sorted(rows, key=lambda row: row.get(field, 0) or 0, reverse=descending)
