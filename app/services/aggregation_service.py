"""Study data aggregation for visualization."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.core.logging import get_logger, log_context
from app.models.aggregation import AggregatedData, AggregationOptions
from app.models.clinical_trials import StudyRecord
from app.models.llm import GroupBy, Metric, SearchIntent
from app.utils.helpers import extract_start_year, format_phase_label

logger = get_logger(__name__)

COUNT_FIELD = "trial_count"
PROPORTION_FIELD = "proportion"
UNKNOWN_LABEL = "Unknown"
NOT_SPECIFIED_LABEL = "Not Specified"
OTHER_LABEL = "Other"

GROUP_BY_DISPATCH: dict[GroupBy, str] = {
    "year": "count_by_year",
    "phase": "count_by_phase",
    "sponsor": "count_by_sponsor",
    "country": "count_by_country",
    "status": "count_by_status",
    "intervention": "count_by_intervention",
}


def count_by_year(studies: list[StudyRecord]) -> list[dict[str, Any]]:
    """Count studies grouped by start year."""
    counter: Counter[int] = Counter()
    for study in studies:
        year = extract_start_year(study.start_date)
        if year is not None:
            counter[year] += 1

    return [
        {"year": year, COUNT_FIELD: count}
        for year, count in sorted(counter.items())
    ]


def count_by_phase(studies: list[StudyRecord]) -> list[dict[str, Any]]:
    """Count studies grouped by trial phase."""
    counter: Counter[str] = Counter()
    for study in studies:
        phases = study.phases or [NOT_SPECIFIED_LABEL]
        for phase in phases:
            counter[format_phase_label(phase)] += 1

    return _rows_from_counter(counter, "phase")


def count_by_sponsor(
    studies: list[StudyRecord],
    *,
    top_n: int = 20,
    include_other_bucket: bool = True,
) -> list[dict[str, Any]]:
    """Count studies grouped by lead sponsor."""
    counter: Counter[str] = Counter()
    for study in studies:
        sponsor = study.sponsor or NOT_SPECIFIED_LABEL
        counter[sponsor] += 1

    return _rows_from_counter(
        counter,
        "sponsor",
        top_n=top_n,
        include_other_bucket=include_other_bucket,
    )


def count_by_country(
    studies: list[StudyRecord],
    *,
    top_n: int = 20,
    include_other_bucket: bool = True,
) -> list[dict[str, Any]]:
    """Count studies grouped by location country."""
    counter: Counter[str] = Counter()
    for study in studies:
        countries = study.countries or [NOT_SPECIFIED_LABEL]
        for country in countries:
            counter[country] += 1

    return _rows_from_counter(
        counter,
        "country",
        top_n=top_n,
        include_other_bucket=include_other_bucket,
    )


def count_by_status(studies: list[StudyRecord]) -> list[dict[str, Any]]:
    """Count studies grouped by overall status."""
    counter: Counter[str] = Counter()
    for study in studies:
        status = _format_status_label(study.overall_status)
        counter[status] += 1

    return _rows_from_counter(counter, "status")


def count_by_intervention(
    studies: list[StudyRecord],
    *,
    top_n: int = 20,
    include_other_bucket: bool = True,
) -> list[dict[str, Any]]:
    """Count studies grouped by intervention name."""
    counter: Counter[str] = Counter()
    for study in studies:
        interventions = study.interventions or [NOT_SPECIFIED_LABEL]
        for intervention in interventions:
            counter[intervention] += 1

    return _rows_from_counter(
        counter,
        "intervention",
        top_n=top_n,
        include_other_bucket=include_other_bucket,
    )


def apply_metric(rows: list[dict[str, Any]], metric: Metric) -> list[dict[str, Any]]:
    """Apply count or proportion metric to aggregated rows."""
    if metric == "trial_count":
        return rows

    total = sum(row.get(COUNT_FIELD, 0) for row in rows)
    if total == 0:
        return [{**row, PROPORTION_FIELD: 0.0} for row in rows]

    return [
        {
            **row,
            PROPORTION_FIELD: round(row.get(COUNT_FIELD, 0) / total, 4),
        }
        for row in rows
    ]


class AggregationService:
    """Aggregate raw study records into visualization-ready rows."""

    def aggregate(
        self,
        studies: list[StudyRecord],
        intent: SearchIntent,
        *,
        options: AggregationOptions | None = None,
    ) -> AggregatedData:
        """Aggregate studies according to search intent."""
        resolved_options = options or AggregationOptions()
        notes: list[str] = []

        log_context(
            logger,
            "Aggregating studies",
            study_count=len(studies),
            group_by=intent.group_by,
            metric=intent.metric,
        )

        rows = self._dispatch(studies, intent.group_by, resolved_options)
        rows = apply_metric(rows, intent.metric)

        if intent.group_by == "year":
            skipped = len(studies) - sum(row[COUNT_FIELD] for row in rows)
            if skipped:
                notes.append(
                    f"Excluded {skipped} studies without a parseable start year."
                )
            if intent.start_year is not None or intent.end_year is not None:
                rows = _filter_year_rows(rows, intent.start_year, intent.end_year)

        if intent.metric == "proportion":
            notes.append("Proportions are computed over aggregated buckets.")

        result = AggregatedData(
            group_by=intent.group_by,
            metric=intent.metric,
            rows=rows,
            record_count=len(studies),
            notes=notes,
        )

        log_context(
            logger,
            "Aggregation completed",
            row_count=len(result.rows),
            group_by=result.group_by,
        )
        return result

    def _dispatch(
        self,
        studies: list[StudyRecord],
        group_by: GroupBy,
        options: AggregationOptions,
    ) -> list[dict[str, Any]]:
        """Route aggregation to the appropriate grouping function."""
        if group_by == "year":
            return count_by_year(studies)
        if group_by == "phase":
            return count_by_phase(studies)
        if group_by == "sponsor":
            return count_by_sponsor(
                studies,
                top_n=options.top_n,
                include_other_bucket=options.include_other_bucket,
            )
        if group_by == "country":
            return count_by_country(
                studies,
                top_n=options.top_n,
                include_other_bucket=options.include_other_bucket,
            )
        if group_by == "status":
            return count_by_status(studies)
        if group_by == "intervention":
            return count_by_intervention(
                studies,
                top_n=options.top_n,
                include_other_bucket=options.include_other_bucket,
            )
        raise ValueError(f"Unsupported group_by dimension: {group_by}")


def _rows_from_counter(
    counter: Counter[str],
    label_field: str,
    *,
    top_n: int | None = None,
    include_other_bucket: bool = False,
) -> list[dict[str, Any]]:
    """Convert a counter to sorted aggregation rows."""
    if not counter:
        return []

    ranked = counter.most_common()
    if top_n is not None and len(ranked) > top_n:
        visible = ranked[:top_n]
        if include_other_bucket:
            other_count = sum(count for _, count in ranked[top_n:])
            if other_count:
                visible.append((OTHER_LABEL, other_count))
        ranked = visible

    return [
        {label_field: label, COUNT_FIELD: count}
        for label, count in ranked
    ]


def _filter_year_rows(
    rows: list[dict[str, Any]],
    start_year: int | None,
    end_year: int | None,
) -> list[dict[str, Any]]:
    """Restrict year rows to an optional year range."""
    filtered: list[dict[str, Any]] = []
    for row in rows:
        year = row.get("year")
        if not isinstance(year, int):
            continue
        if start_year is not None and year < start_year:
            continue
        if end_year is not None and year > end_year:
            continue
        filtered.append(row)
    return filtered


def _format_status_label(status: str | None) -> str:
    """Convert API status codes to readable labels."""
    if not status:
        return NOT_SPECIFIED_LABEL
    return status.replace("_", " ").title()
