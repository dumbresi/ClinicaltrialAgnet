"""Visualization type selection and spec generation."""

from __future__ import annotations

from app.core.exceptions import InvalidVisualizationError
from app.core.logging import get_logger, log_context
from app.models.aggregation import AggregatedData
from app.models.llm import GroupBy, SearchIntent, VisualizationHint
from app.models.response import (
    EncodingChannel,
    MetaData,
    VisualizationEncoding,
    VisualizationResponse,
    VisualizationSpec,
    VisualizationType,
)
from app.services.aggregation_service import COUNT_FIELD, PROPORTION_FIELD

logger = get_logger(__name__)

GROUP_BY_LABELS: dict[GroupBy, str] = {
    "year": "Over Time",
    "phase": "by Phase",
    "sponsor": "by Sponsor",
    "country": "by Country",
    "status": "by Status",
    "intervention": "by Intervention",
}

GROUP_BY_FIELD: dict[GroupBy, str] = {
    "year": "year",
    "phase": "phase",
    "sponsor": "sponsor",
    "country": "country",
    "status": "status",
    "intervention": "intervention",
}

HINT_TO_TYPE: dict[VisualizationHint, VisualizationType] = {
    "time_series": "line_chart",
    "bar_chart": "bar_chart",
    "pie_chart": "pie_chart",
    "map": "map",
    "network_graph": "network_graph",
}


class VisualizationService:
    """Select chart types and build frontend-ready visualization specs."""

    def build_spec(
        self,
        aggregated: AggregatedData,
        intent: SearchIntent,
    ) -> VisualizationSpec:
        """Build a visualization specification from aggregated data."""
        if not aggregated.rows:
            raise InvalidVisualizationError("Cannot build visualization from empty data")

        chart_type = select_visualization_type(aggregated, intent)
        value_field = _value_field(aggregated.metric)
        title = build_title(intent, chart_type)
        encoding = build_encoding(chart_type, aggregated.group_by, value_field)

        log_context(
            logger,
            "Visualization spec built",
            chart_type=chart_type,
            group_by=aggregated.group_by,
            metric=aggregated.metric,
            row_count=len(aggregated.rows),
        )

        return VisualizationSpec(
            type=chart_type,
            title=title,
            encoding=encoding,
            data=aggregated.rows,
        )

    def build_response(
        self,
        aggregated: AggregatedData,
        intent: SearchIntent,
    ) -> VisualizationResponse:
        """Build the full API response including metadata."""
        visualization = self.build_spec(aggregated, intent)
        filters = intent.active_filters()
        filters["group_by"] = intent.group_by
        filters["metric"] = intent.metric

        notes = list(aggregated.notes)
        if intent.visualization_hint != _hint_for_type(visualization.type):
            notes.append(
                f"Visualization type '{visualization.type}' selected from "
                f"group_by='{intent.group_by}' and metric='{intent.metric}'."
            )

        meta = MetaData(
            filters=filters,
            record_count=aggregated.record_count,
            source="ClinicalTrials.gov",
            notes=notes,
        )
        return VisualizationResponse(visualization=visualization, meta=meta)


def select_visualization_type(
    aggregated: AggregatedData,
    intent: SearchIntent,
) -> VisualizationType:
    """Choose the best visualization type for aggregated data and intent."""
    if intent.visualization_hint == "network_graph":
        raise InvalidVisualizationError(
            "Network graphs require relationship data not produced by current aggregations"
        )

    if aggregated.metric == "proportion":
        if intent.group_by == "country" and intent.visualization_hint == "map":
            return "map"
        return "pie_chart"

    if intent.group_by == "year":
        return "line_chart"

    if intent.group_by == "country":
        return "map"

    if intent.visualization_hint == "pie_chart":
        return "pie_chart"

    if intent.visualization_hint == "bar_chart":
        return "bar_chart"

    if intent.visualization_hint == "map" and intent.group_by == "country":
        return "map"

    return "bar_chart"


def build_title(intent: SearchIntent, chart_type: VisualizationType) -> str:
    """Generate a human-readable chart title."""
    subject = _subject_phrase(intent)
    suffix = GROUP_BY_LABELS[intent.group_by]

    if chart_type == "pie_chart" and intent.metric == "proportion":
        return f"{subject} Distribution {suffix}"

    return f"{subject} {suffix}"


def build_encoding(
    chart_type: VisualizationType,
    group_by: GroupBy,
    value_field: str,
) -> VisualizationEncoding:
    """Build field-to-channel encoding for the selected chart type."""
    category_field = GROUP_BY_FIELD[group_by]
    value_channel = EncodingChannel(field=value_field, type="quantitative")

    if chart_type == "line_chart":
        return VisualizationEncoding(
            x=EncodingChannel(field=category_field, label="Year", type="temporal"),
            y=EncodingChannel(field=value_field, label="Trial Count", type="quantitative"),
        )

    if chart_type == "bar_chart":
        return VisualizationEncoding(
            x=EncodingChannel(field=category_field, type="nominal"),
            y=value_channel,
        )

    if chart_type == "pie_chart":
        return VisualizationEncoding(
            label=EncodingChannel(field=category_field, type="nominal"),
            value=value_channel,
        )

    if chart_type == "map":
        return VisualizationEncoding(
            geo=EncodingChannel(field=category_field, type="nominal"),
            value=value_channel,
        )

    raise InvalidVisualizationError(f"Unsupported visualization type: {chart_type}")


def _value_field(metric: str) -> str:
    """Return the data field used for the primary value channel."""
    return PROPORTION_FIELD if metric == "proportion" else COUNT_FIELD


def _subject_phrase(intent: SearchIntent) -> str:
    """Build the subject fragment used in chart titles."""
    if intent.condition and intent.drug:
        return f"Trials for {intent.drug} in {intent.condition}"
    if intent.condition:
        return f"{intent.condition} Trials"
    if intent.drug:
        return f"Trials for {intent.drug}"
    if intent.sponsor:
        return f"Trials Sponsored by {intent.sponsor}"
    return "Clinical Trials"


def _hint_for_type(chart_type: VisualizationType) -> VisualizationHint:
    """Map a visualization type back to its default hint."""
    for hint, mapped_type in HINT_TO_TYPE.items():
        if mapped_type == chart_type:
            return hint
    return "bar_chart"
