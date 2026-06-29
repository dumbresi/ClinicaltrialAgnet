"""Proportion metric operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.operations.base import COUNT_FIELD, PROPORTION_FIELD
from app.models.execution_plan import AggregationStep


class ProportionOperation:
    """Add proportion field based on trial_count."""

    name = "proportion"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        value_field = step.params.get("value_field", COUNT_FIELD)
        total = sum(row.get(value_field, 0) or 0 for row in rows)
        if total == 0:
            return [{**row, PROPORTION_FIELD: 0.0} for row in rows]
        return [
            {
                **row,
                PROPORTION_FIELD: round((row.get(value_field, 0) or 0) / total, 4),
            }
            for row in rows
        ]
