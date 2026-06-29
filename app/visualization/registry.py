"""Visualization builder registry and base types."""

from __future__ import annotations

from typing import Protocol

from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import VisualizationSpec


class VisualizationBuilder(Protocol):
    """Protocol for pluggable visualization builders."""

    chart_type: str

    def build(
        self,
        plan: ExecutionPlan,
        aggregated: AggregatedData,
    ) -> VisualizationSpec:
        """Build a visualization spec from plan and aggregated data."""
        ...


class VisualizationRegistry:
    """Registry mapping chart types to visualization builders."""

    def __init__(self) -> None:
        self._builders: dict[str, VisualizationBuilder] = {}

    def register(self, builder: VisualizationBuilder) -> None:
        self._builders[builder.chart_type] = builder

    def get(self, chart_type: str) -> VisualizationBuilder:
        if chart_type not in self._builders:
            raise KeyError(f"Unknown visualization type: {chart_type}")
        return self._builders[chart_type]

    @property
    def chart_types(self) -> frozenset[str]:
        return frozenset(self._builders)


def build_default_registry() -> VisualizationRegistry:
    """Construct the default visualization registry."""
    from app.visualization.builders import (
        BarChartBuilder,
        GroupedBarChartBuilder,
        KpiBuilder,
        LineChartBuilder,
        MapBuilder,
        NetworkGraphBuilder,
        PieChartBuilder,
        ScatterPlotBuilder,
        StackedBarChartBuilder,
        TableBuilder,
    )

    registry = VisualizationRegistry()
    for builder in (
        LineChartBuilder(),
        BarChartBuilder(),
        GroupedBarChartBuilder(),
        StackedBarChartBuilder(),
        PieChartBuilder(),
        ScatterPlotBuilder(),
        TableBuilder(),
        MapBuilder(),
        NetworkGraphBuilder(),
        KpiBuilder(),
    ):
        registry.register(builder)
    return registry
