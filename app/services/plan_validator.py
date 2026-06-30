"""Post-planner validation for execution plans."""

from __future__ import annotations

import re

from app.core.exceptions import InvalidExecutionPlanError
from app.models.execution_plan import ExecutionPlan

REGION_LIKE_LOCATIONS = frozenset(
    {
        "africa",
        "asia",
        "europe",
        "north america",
        "south america",
        "latin america",
        "middle east",
        "oceania",
        "worldwide",
        "global",
    }
)

_OFF_TOPIC_FALLBACK_SIGNATURES = (
    {"intent": "trend", "group_by": "year", "visualization": "line_chart"},
    {"intent": "single", "group_by": "year", "visualization": "line_chart"},
)

_CLINICAL_TRIAL_QUERY_PATTERNS = (
    r"\bclinical\s+trial",
    r"\btrials?\b",
    r"\bstudies\b",
    r"\bstudy\b",
    r"\bdrugs?\b",
    r"\bconditions?\b",
    r"\bdiseases?\b",
    r"\bsponsors?\b",
    r"\bphase\b",
    r"\brecruit",
    r"\binterventions?\b",
    r"\bnct\b",
    r"\benrollment\b",
    r"\bpharma",
)


def validate_execution_plan(plan: ExecutionPlan, *, query_text: str = "") -> None:
    """Reject plans that lack actionable clinical trial search criteria."""
    if plan.has_search_criteria():
        return

    if plan.allows_unscoped_search():
        if not _query_mentions_clinical_trials(query_text):
            raise InvalidExecutionPlanError(
                "The query does not appear to be about clinical trial search. "
                "Ask about trial counts, trends, comparisons, or distributions "
                "for a condition, drug, sponsor, or location."
            )
        return

    if _looks_like_off_topic_fallback(plan):
        raise InvalidExecutionPlanError(
            "The query does not appear to be about clinical trial search. "
            "Ask about trial counts, trends, comparisons, or distributions "
            "for a condition, drug, sponsor, or location."
        )

    raise InvalidExecutionPlanError(
        "Could not identify clinical trial search criteria in the query. "
        "Specify a condition, drug, sponsor, country, or other filter."
    )


def collect_plan_warnings(plan: ExecutionPlan) -> list[str]:
    """Return non-fatal warnings about potentially ambiguous plan fields."""
    warnings: list[str] = []

    country = plan.filters.country
    if country and _is_region_like(country):
        warnings.append(
            f"Location filter '{country}' looks like a region, not a single country. "
            "ClinicalTrials.gov location search works best with specific country names."
        )

    for entity in plan.entities:
        if entity.type == "country" and _is_region_like(entity.value):
            warnings.append(
                f"Comparison location '{entity.value}' looks like a region. "
                "Results may be incomplete unless split into specific countries."
            )

    if plan.allows_unscoped_search() and not plan.has_search_criteria():
        warnings.append(
            "No search filters were applied; results reflect a broad ClinicalTrials.gov search."
        )

    return warnings


def _looks_like_off_topic_fallback(plan: ExecutionPlan) -> bool:
    if plan.has_search_criteria() or plan.comparison:
        return False

    for signature in _OFF_TOPIC_FALLBACK_SIGNATURES:
        if all(getattr(plan, field) == value for field, value in signature.items()):
            return True

    return False


def _is_region_like(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    if normalized in REGION_LIKE_LOCATIONS:
        return True
    return normalized.startswith("european union") or normalized in {"eu", "us and europe"}


def _query_mentions_clinical_trials(query_text: str) -> bool:
    normalized = query_text.strip().lower()
    if not normalized:
        return False
    return any(re.search(pattern, normalized) for pattern in _CLINICAL_TRIAL_QUERY_PATTERNS)
