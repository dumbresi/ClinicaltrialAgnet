"""External API clients."""

from app.clients.clinical_trials_client import (
    ClinicalTrialsClient,
    ClinicalTrialsClientProtocol,
    build_base_params,
    parse_study_record,
)
from app.clients.openai_client import OpenAIClient, OpenAIClientProtocol

__all__ = [
    "ClinicalTrialsClient",
    "ClinicalTrialsClientProtocol",
    "OpenAIClient",
    "OpenAIClientProtocol",
    "build_base_params",
    "parse_study_record",
]
