"""Count aggregation operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.operations.base import COUNT_FIELD
from app.models.execution_plan import AggregationStep


class CountOperation:
    """Count unique studies when no grouping dimensions are specified."""

    name = "count"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        if rows:
            return rows
        unique_ncts = {tagged.study.nct_id for tagged in ctx.studies if tagged.study.nct_id}
        return [{COUNT_FIELD: len(unique_ncts)}]
