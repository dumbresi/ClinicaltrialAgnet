"""Aggregation pipeline builder and execution engine."""

from __future__ import annotations

from typing import Any

from app.aggregation.context import AggregationContext, TaggedStudy
from app.aggregation.operations.base import COUNT_FIELD
from app.aggregation.registry import AggregationRegistry, build_default_registry
from app.core.logging import get_logger, log_context
from app.models.aggregation import AggregatedData, AggregationOptions
from app.models.execution_plan import AggregationStep, ExecutionPlan

logger = get_logger(__name__)

HIGH_CARDINALITY_DIMENSIONS = frozenset({"sponsor", "country", "intervention"})


class AggregationEngine:
    """Execute aggregation pipelines derived from execution plans."""

    def __init__(self, registry: AggregationRegistry | None = None) -> None:
        self._registry = registry or build_default_registry()

    def aggregate(
        self,
        studies: list[TaggedStudy],
        plan: ExecutionPlan,
        *,
        options: AggregationOptions | None = None,
    ) -> AggregatedData:
        """Run the aggregation pipeline for tagged studies and an execution plan."""
        resolved_options = options or AggregationOptions()
        ctx = AggregationContext(studies=studies, plan=plan)
        pipeline = self._derive_pipeline(plan, resolved_options)

        log_context(
            logger,
            "Running aggregation pipeline",
            study_count=len(studies),
            pipeline=[step.operation for step in pipeline],
        )

        rows: list[dict[str, Any]] = []
        for step in pipeline:
            rows = self._registry.apply_step(ctx, rows, step)

        notes = list(ctx.notes)
        if plan.metric == "proportion":
            notes.append("Proportions are computed over aggregated buckets.")

        group_by = plan.group_by or "none"
        if plan.comparison and plan.series_field():
            group_by = f"{plan.series_field()}+{group_by}" if plan.group_by else plan.series_field()

        result = AggregatedData(
            group_by=group_by,  # type: ignore[arg-type]
            metric=plan.metric,  # type: ignore[arg-type]
            rows=rows,
            record_count=len(studies),
            notes=notes,
            series_field=plan.series_field(),
            comparison=plan.comparison,
        )

        log_context(
            logger,
            "Aggregation completed",
            row_count=len(result.rows),
            aggregation=plan.aggregation_label(),
        )
        return result

    def _derive_pipeline(
        self,
        plan: ExecutionPlan,
        options: AggregationOptions,
    ) -> list[AggregationStep]:
        """Build a default pipeline from plan fields."""
        if plan.intent == "relationship" or plan.visualization == "network_graph":
            return [
                AggregationStep(
                    operation="network_edges",
                    params={
                        "source": plan.network_source or "intervention",
                        "target": plan.network_target or "sponsor",
                    },
                ),
                AggregationStep(operation="sort", params={"field": COUNT_FIELD, "descending": True}),
                AggregationStep(operation="top_n", params={"n": options.top_n}),
            ]

        if plan.group_by is None and not plan.comparison:
            return [AggregationStep(operation="count")]

        fields: list[str] = []
        series = plan.series_field()
        if series:
            fields.append(series)
        if plan.group_by:
            fields.append(plan.group_by)

        pipeline: list[AggregationStep] = [
            AggregationStep(
                operation="group_by",
                params={"fields": fields, "metric": plan.metric},
            ),
        ]

        if plan.group_by in HIGH_CARDINALITY_DIMENSIONS:
            pipeline.append(
                AggregationStep(
                    operation="top_n",
                    params={
                        "n": options.top_n,
                        "include_other_bucket": options.include_other_bucket,
                        "label_field": plan.group_by,
                    },
                )
            )

        if plan.metric == "proportion":
            pipeline.append(AggregationStep(operation="proportion"))

        sort_field = plan.group_by or series or COUNT_FIELD
        pipeline.append(
            AggregationStep(
                operation="sort",
                params={"field": sort_field, "descending": sort_field == COUNT_FIELD},
            )
        )

        return pipeline
