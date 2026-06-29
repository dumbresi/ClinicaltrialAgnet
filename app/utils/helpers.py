"""Shared helper functions."""

import json
import re
from pathlib import Path

from app.models.llm import SearchIntent
from app.models.request import UserQuery

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

PHASE_TOKEN_MAP = {
    "EARLY PHASE 1": "EARLY_PHASE1",
    "EARLY_PHASE1": "EARLY_PHASE1",
    "PHASE 0": "EARLY_PHASE1",
    "PHASE 1": "PHASE1",
    "PHASE1": "PHASE1",
    "PHASE I": "PHASE1",
    "PHASE 1/PHASE 2": "PHASE1",
    "PHASE 2": "PHASE2",
    "PHASE2": "PHASE2",
    "PHASE II": "PHASE2",
    "PHASE 2/PHASE 3": "PHASE2",
    "PHASE 3": "PHASE3",
    "PHASE3": "PHASE3",
    "PHASE III": "PHASE3",
    "PHASE 4": "PHASE4",
    "PHASE4": "PHASE4",
    "PHASE IV": "PHASE4",
    "NA": "NA",
    "N/A": "NA",
}


def load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_intent_user_message(user_query: UserQuery) -> str:
    """Build the JSON payload sent to the intent parser."""
    payload: dict[str, object] = {"query": user_query.query}
    explicit_filters = user_query.explicit_filters()
    if explicit_filters:
        payload["explicit_filters"] = explicit_filters
    return json.dumps(payload, indent=2, ensure_ascii=False)


def merge_explicit_filters(intent: SearchIntent, user_query: UserQuery) -> SearchIntent:
    """Apply user-provided structured filters, overriding LLM output."""
    updates: dict[str, object] = {}

    if user_query.drug_name is not None:
        updates["drug"] = user_query.drug_name
    if user_query.condition is not None:
        updates["condition"] = user_query.condition
    if user_query.trial_phase is not None:
        updates["phase"] = user_query.trial_phase
    if user_query.sponsor is not None:
        updates["sponsor"] = user_query.sponsor
    if user_query.country is not None:
        updates["country"] = user_query.country
    if user_query.start_year is not None:
        updates["start_year"] = user_query.start_year
    if user_query.end_year is not None:
        updates["end_year"] = user_query.end_year

    if not updates:
        return intent

    return intent.model_copy(update=updates)


def normalize_phase_token(phase: str) -> str | None:
    """Convert human-readable phase text to ClinicalTrials.gov phase token."""
    normalized = re.sub(r"\s+", " ", phase.strip().upper())
    if normalized in PHASE_TOKEN_MAP:
        return PHASE_TOKEN_MAP[normalized]

    compact = normalized.replace(" ", "")
    if compact in PHASE_TOKEN_MAP:
        return PHASE_TOKEN_MAP[compact]

    if re.fullmatch(r"PHASE\d", compact):
        return compact

    return None


PHASE_LABELS = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE2": "Phase 2",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
    "NA": "Not Applicable",
}


def format_phase_label(phase: str) -> str:
    """Convert API phase tokens to human-readable labels."""
    token = phase.strip().upper().replace(" ", "_")
    if token in PHASE_LABELS:
        return PHASE_LABELS[token]
    return phase.strip() or "Not Specified"


def extract_start_year(start_date: str | None) -> int | None:
    """Extract the four-digit start year from an API date string."""
    if not start_date:
        return None
    match = re.match(r"(\d{4})", start_date.strip())
    if not match:
        return None
    return int(match.group(1))
