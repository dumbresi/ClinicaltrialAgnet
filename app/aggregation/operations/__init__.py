"""Built-in aggregation operations."""

from __future__ import annotations

from app.aggregation.operations.average import AverageOperation
from app.aggregation.operations.count import CountOperation
from app.aggregation.operations.group_by import GroupByOperation
from app.aggregation.operations.histogram import HistogramOperation
from app.aggregation.operations.median import MedianOperation
from app.aggregation.operations.network_edges import NetworkEdgesOperation
from app.aggregation.operations.proportion import ProportionOperation
from app.aggregation.operations.sort import SortOperation
from app.aggregation.operations.sum import SumOperation
from app.aggregation.operations.top_n import TopNOperation
from app.aggregation.operations.unique import UniqueOperation

__all__ = [
    "AverageOperation",
    "CountOperation",
    "GroupByOperation",
    "HistogramOperation",
    "MedianOperation",
    "NetworkEdgesOperation",
    "ProportionOperation",
    "SortOperation",
    "SumOperation",
    "TopNOperation",
    "UniqueOperation",
]
