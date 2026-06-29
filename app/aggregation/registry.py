"""Aggregation operation registry and base types."""

from __future__ import annotations

from typing import Any, Protocol

from app.aggregation.context import AggregationContext
from app.models.execution_plan import AggregationStep


class AggregationOperation(Protocol):
    """Protocol for pluggable aggregation operations."""

    name: str

    def apply(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        """Transform rows using the aggregation context."""
        ...


class AggregationRegistry:
    """Registry mapping operation names to aggregation strategies."""

    def __init__(self) -> None:
        self._operations: dict[str, AggregationOperation] = {}

    def register(self, operation: AggregationOperation) -> None:
        self._operations[operation.name] = operation

    def get(self, name: str) -> AggregationOperation:
        if name not in self._operations:
            raise KeyError(f"Unknown aggregation operation: {name}")
        return self._operations[name]

    def apply_step(
        self,
        ctx: AggregationContext,
        rows: list[dict[str, Any]],
        step: AggregationStep,
    ) -> list[dict[str, Any]]:
        operation = self.get(step.operation)
        merged_params = dict(step.params)
        if step.field:
            merged_params.setdefault("field", step.field)
        merged_step = step.model_copy(update={"params": merged_params})
        return operation.apply(ctx, rows, merged_step)

    @property
    def operations(self) -> frozenset[str]:
        return frozenset(self._operations)


def build_default_registry() -> AggregationRegistry:
    """Construct the default aggregation registry with all built-in operations."""
    from app.aggregation.operations import (
        AverageOperation,
        CountOperation,
        GroupByOperation,
        MedianOperation,
        NetworkEdgesOperation,
        ProportionOperation,
        SortOperation,
        SumOperation,
        TopNOperation,
        UniqueOperation,
    )
    from app.aggregation.operations.histogram import make_histogram_operation

    registry = AggregationRegistry()
    for operation in (
        CountOperation(),
        GroupByOperation(),
        SumOperation(),
        AverageOperation(),
        MedianOperation(),
        UniqueOperation(),
        TopNOperation(),
        SortOperation(),
        ProportionOperation(),
        NetworkEdgesOperation(),
    ):
        registry.register(operation)

    for histogram_name in (
        "date_histogram",
        "country_histogram",
        "phase_histogram",
        "status_histogram",
        "sponsor_histogram",
    ):
        registry.register(make_histogram_operation(histogram_name))
    return registry
