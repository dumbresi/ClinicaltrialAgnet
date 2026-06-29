"""Shared helpers for visualization builders."""

from __future__ import annotations

from app.aggregation.operations.base import (
    COUNT_FIELD,
    ENROLLMENT_AVG_FIELD,
    ENROLLMENT_SUM_FIELD,
    PROPORTION_FIELD,
)
from app.models.aggregation import AggregatedData
from app.models.execution_plan import ExecutionPlan
from app.models.response import EncodingChannel

GROUP_BY_LABELS: dict[str, str] = {
    "year": "Over Time",
    "phase": "by Phase",
    "sponsor": "by Sponsor",
    "country": "by Country",
    "status": "by Status",
    "intervention": "by Intervention",
    "enrollment": "by Enrollment",
    "drug": "by Drug",
    "condition": "by Condition",
}

DIMENSION_LABELS: dict[str, str] = {
    "year": "Year",
    "phase": "Phase",
    "sponsor": "Sponsor",
    "country": "Country",
    "status": "Status",
    "intervention": "Intervention",
    "enrollment": "Enrollment",
    "drug": "Drug",
    "condition": "Condition",
}


def value_field(plan: ExecutionPlan) -> str:
    """Return the primary value field for the plan metric."""
    if plan.metric == "proportion":
        return PROPORTION_FIELD
    if plan.metric == "enrollment_sum":
        return ENROLLMENT_SUM_FIELD
    if plan.metric == "enrollment_average":
        return ENROLLMENT_AVG_FIELD
    return COUNT_FIELD


def value_label(plan: ExecutionPlan) -> str:
    """Return a human-readable label for the value field."""
    labels = {
        "trial_count": "Trial Count",
        "proportion": "Proportion",
        "enrollment_sum": "Total Enrollment",
        "enrollment_average": "Average Enrollment",
    }
    return labels.get(plan.metric, "Value")


def category_field(plan: ExecutionPlan, aggregated: AggregatedData) -> str:
    """Return the primary category field for encoding."""
    if plan.group_by:
        return plan.group_by
    if aggregated.rows:
        for key in aggregated.rows[0]:
            if key not in {
                COUNT_FIELD,
                PROPORTION_FIELD,
                ENROLLMENT_SUM_FIELD,
                ENROLLMENT_AVG_FIELD,
                "source",
                "target",
            }:
                return key
    return "category"


def encoding_channel(field: str, *, label: str | None = None, channel_type: str | None = None) -> EncodingChannel:
    """Create an encoding channel."""
    return EncodingChannel(field=field, label=label, type=channel_type)  # type: ignore[arg-type]


def build_title(plan: ExecutionPlan) -> str:
    """Generate a human-readable chart title."""
    if plan.comparison and plan.entities:
        names = " vs ".join(entity.display_label for entity in plan.entities)
        if plan.group_by:
            suffix = GROUP_BY_LABELS.get(plan.group_by, f"by {plan.group_by.title()}")
            return f"{names} Trials {suffix}"
        return f"{names} Comparison"

    subject = _subject_phrase(plan)
    if plan.visualization == "network_graph":
        source = plan.network_source or "source"
        target = plan.network_target or "target"
        source_label = DIMENSION_LABELS.get(source, source.replace("_", " ").title())
        target_label = DIMENSION_LABELS.get(target, target.replace("_", " ").title())
        return f"{subject}: {source_label} & {target_label}"

    if plan.group_by:
        suffix = GROUP_BY_LABELS.get(plan.group_by, f"by {plan.group_by.title()}")
        if plan.metric == "proportion":
            return f"{subject} Distribution {suffix}"
        return f"{subject} {suffix}"

    return f"{subject} Summary"


def _subject_phrase(plan: ExecutionPlan) -> str:
    filters = plan.filters
    if filters.condition and filters.drug:
        return f"Trials for {filters.drug} in {filters.condition}"
    if filters.condition:
        return f"{filters.condition.title()} Trials"
    if filters.drug:
        return f"Trials for {filters.drug}"
    if filters.sponsor:
        return f"Trials Sponsored by {filters.sponsor}"
    if plan.entities:
        return f"Trials for {plan.entities[0].display_label}"
    return "Clinical Trials"
