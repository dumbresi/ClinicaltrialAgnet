"""Group-by aggregation with unique NCT counting."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.dimensions import extract_dimension_values
from app.aggregation.operations.base import COUNT_FIELD, ENROLLMENT_AVG_FIELD, ENROLLMENT_SUM_FIELD
from app.models.execution_plan import AggregationStep


class GroupByOperation:
    """Group studies by one or more dimensions, counting unique NCT IDs."""

    name = "group_by"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        fields: list[str] = step.params.get("fields") or []
        if step.field:
            fields = [step.field]
        if not fields:
            fields = _default_fields(ctx)

        metric = step.params.get("metric", ctx.plan.metric)
        buckets: dict[tuple[Any, ...], set[str]] = defaultdict(set)
        enrollment_values: dict[tuple[Any, ...], list[int]] = defaultdict(list)

        for tagged in ctx.studies:
            nct_id = tagged.study.nct_id
            if not nct_id:
                continue

            dimension_values: dict[str, list[Any]] = defaultdict(list)
            for field in fields:
                for dim_name, value in extract_dimension_values(tagged, field):
                    dimension_values[dim_name].append(value)

            if not dimension_values:
                continue

            keys = _cartesian_keys(fields, dimension_values)
            for key in keys:
                buckets[key].add(nct_id)
                if metric in ("enrollment_sum", "enrollment_average"):
                    enrollment = tagged.study.enrollment
                    if enrollment is not None:
                        enrollment_values[key].append(enrollment)

        result: list[dict[str, Any]] = []
        for key, nct_ids in buckets.items():
            row = dict(zip(fields, key, strict=False))
            row[COUNT_FIELD] = len(nct_ids)
            if metric == "enrollment_sum":
                row[ENROLLMENT_SUM_FIELD] = sum(enrollment_values.get(key, []))
            elif metric == "enrollment_average":
                values = enrollment_values.get(key, [])
                row[ENROLLMENT_AVG_FIELD] = (
                    round(sum(values) / len(values), 2) if values else 0.0
                )
            result.append(row)

        return result


def _default_fields(ctx: AggregationContext) -> list[str]:
    fields: list[str] = []
    series = ctx.plan.series_field()
    if series:
        fields.append(series)
    if ctx.plan.group_by:
        fields.append(ctx.plan.group_by)
    return fields or ["trial_count"]


def _cartesian_keys(
    fields: list[str],
    dimension_values: dict[str, list[Any]],
) -> list[tuple[Any, ...]]:
    if not fields:
        return [()]

    result: list[tuple[Any, ...]] = [()]
    for field in fields:
        values = dimension_values.get(field) or ["Unknown"]
        next_result: list[tuple[Any, ...]] = []
        for prefix in result:
            for value in values:
                next_result.append((*prefix, value))
        result = next_result
    return result
