"""Incoming request models."""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserQuery(BaseModel):
    """Natural language query with optional structured filters.

    Fields
    ------
    query:
        Required natural language question about clinical trials.
    drug_name:
        Optional intervention or drug name to constrain the search.
    condition:
        Optional disease or condition name.
    trial_phase:
        Optional trial phase filter (e.g. ``"Phase 2"``).
    sponsor:
        Optional sponsor or organization name.
    country:
        Optional country or location filter.
    start_year:
        Optional inclusive lower bound on study start year.
    end_year:
        Optional inclusive upper bound on study start year.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "query": "How has the number of trials for this drug changed over time?",
                    "drug_name": "Pembrolizumab",
                },
                {
                    "query": "How has the number of breast cancer trials changed over time?",
                },
            ]
        },
    )

    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language clinical trial question.",
    )
    drug_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Optional drug or intervention name.",
    )
    condition: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Optional disease or condition name.",
    )
    trial_phase: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Optional trial phase filter.",
    )
    sponsor: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Optional sponsor or organization name.",
    )
    country: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Optional country or location filter.",
    )
    start_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Optional inclusive lower bound on study start year.",
    )
    end_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Optional inclusive upper bound on study start year.",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_blank(cls, value: str) -> str:
        """Ensure the query is not whitespace-only."""
        if not value.strip():
            raise ValueError("query must not be blank")
        return value

    @model_validator(mode="after")
    def validate_year_range(self) -> Self:
        """Ensure end_year is not before start_year when both are provided."""
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.end_year < self.start_year
        ):
            raise ValueError("end_year must be greater than or equal to start_year")
        return self

    def explicit_filters(self) -> dict[str, Any]:
        """Return user-provided structured filters, omitting null values."""
        filters: dict[str, Any] = {}
        if self.drug_name is not None:
            filters["drug_name"] = self.drug_name
        if self.condition is not None:
            filters["condition"] = self.condition
        if self.trial_phase is not None:
            filters["trial_phase"] = self.trial_phase
        if self.sponsor is not None:
            filters["sponsor"] = self.sponsor
        if self.country is not None:
            filters["country"] = self.country
        if self.start_year is not None:
            filters["start_year"] = self.start_year
        if self.end_year is not None:
            filters["end_year"] = self.end_year
        return filters
