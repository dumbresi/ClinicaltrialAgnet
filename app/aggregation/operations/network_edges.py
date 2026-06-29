"""Network edge aggregation for relationship graphs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.aggregation.context import AggregationContext
from app.aggregation.dimensions import extract_dimension_values
from app.aggregation.operations.base import COUNT_FIELD
from app.models.execution_plan import AggregationStep


class NetworkEdgesOperation:
    """Build co-occurrence edges between two dimensions."""

    name = "network_edges"

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        source_field = (
            step.params.get("source")
            or ctx.plan.network_source
            or "intervention"
        )
        target_field = (
            step.params.get("target")
            or ctx.plan.network_target
            or "sponsor"
        )

        edge_counts: dict[tuple[str, str], set[str]] = defaultdict(set)

        for tagged in ctx.studies:
            nct_id = tagged.study.nct_id
            if not nct_id:
                continue

            sources = {
                str(value)
                for _, value in extract_dimension_values(tagged, source_field)
            }
            targets = {
                str(value)
                for _, value in extract_dimension_values(tagged, target_field)
            }

            for source in sources:
                for target in targets:
                    if source != target:
                        edge_counts[(source, target)].add(nct_id)

        return [
            {
                "source": source,
                "target": target,
                COUNT_FIELD: len(nct_ids),
            }
            for (source, target), nct_ids in sorted(
                edge_counts.items(),
                key=lambda item: len(item[1]),
                reverse=True,
            )
        ]
