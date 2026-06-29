"""Extract dimension values from study records with unique counting."""

from __future__ import annotations

from app.aggregation.context import TaggedStudy
from app.models.execution_plan import GroupByDimension
from app.utils.helpers import (
    extract_start_year,
    format_phase_label,
    format_sponsor_label,
    format_status_label,
    normalize_display_label,
)

NOT_SPECIFIED_LABEL = "Not Specified"
COUNT_FIELD = "trial_count"
PROPORTION_FIELD = "proportion"
ENROLLMENT_FIELD = "enrollment"


def extract_dimension_values(
    tagged: TaggedStudy,
    dimension: str,
) -> list[tuple[str, str | int | float | None]]:
    """Return (field_name, value) pairs for a dimension on a tagged study."""
    study = tagged.study

    if dimension == tagged.series_field and tagged.series:
        return [(dimension, tagged.series)]

    if dimension == "year":
        year = extract_start_year(study.start_date)
        if year is not None:
            return [("year", year)]
        return []

    if dimension == "phase":
        phases = study.phases or []
        if not phases:
            return [("phase", NOT_SPECIFIED_LABEL)]
        return [("phase", format_phase_label(phase)) for phase in _unique_preserve(phases)]

    if dimension == "country":
        countries = study.countries or []
        if not countries:
            return [("country", NOT_SPECIFIED_LABEL)]
        return [
            ("country", normalize_display_label(country))
            for country in _unique_preserve(countries)
        ]

    if dimension == "sponsor":
        return [("sponsor", format_sponsor_label(study.sponsor or NOT_SPECIFIED_LABEL))]

    if dimension == "status":
        return [("status", format_status_label(study.overall_status))]

    if dimension == "intervention":
        interventions = study.interventions or []
        if not interventions:
            return [("intervention", NOT_SPECIFIED_LABEL)]
        return [
            ("intervention", normalize_display_label(intervention))
            for intervention in _unique_preserve(interventions)
        ]

    if dimension == "enrollment":
        if study.enrollment is not None:
            return [("enrollment", study.enrollment)]
        return []

    if dimension in {"drug", "condition", "sponsor", "country", "phase", "status"}:
        if tagged.series and tagged.series_field == dimension:
            return [(dimension, tagged.series)]

    return []


def default_histogram_dimension(operation: str) -> GroupByDimension | None:
    """Map histogram operation names to group_by dimensions."""
    mapping = {
        "date_histogram": "year",
        "phase_histogram": "phase",
        "country_histogram": "country",
        "status_histogram": "status",
        "sponsor_histogram": "sponsor",
    }
    return mapping.get(operation)  # type: ignore[return-value]


def _unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
