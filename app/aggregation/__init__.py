"""Aggregation package."""

from app.aggregation.context import AggregationContext, TaggedStudy
from app.aggregation.engine import AggregationEngine
from app.aggregation.registry import AggregationRegistry, build_default_registry

__all__ = [
    "AggregationContext",
    "AggregationEngine",
    "AggregationRegistry",
    "TaggedStudy",
    "build_default_registry",
]
