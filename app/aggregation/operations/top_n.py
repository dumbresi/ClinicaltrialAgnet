"""Top-N aggregation operation."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.operations.base import COUNT_FIELD, OTHER_LABEL
from app.models.execution_plan import AggregationStep


class TopNOperation:
    """Keep the top N rows by value, optionally bucketing the rest as Other."""

    name = "top_n"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        if not rows:
            return rows

        n: int = step.params.get("n", 20)
        value_field: str = step.params.get("value_field", COUNT_FIELD)
        label_field: str | None = step.params.get("label_field")
        include_other: bool = step.params.get("include_other_bucket", True)

        if not label_field:
            label_field = _infer_label_field(rows[0], value_field)

        if include_other and _label_field_count(rows[0], value_field) > 1:
            include_other = False

        sorted_rows = sorted(
            rows,
            key=lambda row: row.get(value_field, 0) or 0,
            reverse=True,
        )

        if len(sorted_rows) <= n:
            return sorted_rows

        visible = sorted_rows[:n]
        if include_other:
            other_count = sum(row.get(value_field, 0) or 0 for row in sorted_rows[n:])
            if other_count:
                visible.append({label_field: OTHER_LABEL, value_field: other_count})
        return visible


def _infer_label_field(row: dict[str, Any], value_field: str) -> str:
    for key in row:
        if key != value_field:
            return key
    return "category"


def _label_field_count(row: dict[str, Any], value_field: str) -> int:
    return sum(1 for key in row if key != value_field)
