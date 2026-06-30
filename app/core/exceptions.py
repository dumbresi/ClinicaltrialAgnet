"""Application-specific exceptions."""


class AppError(Exception):
    """Base exception for application errors."""


class OpenAIServiceError(AppError):
    """Raised when OpenAI intent extraction fails."""


class InvalidOpenAIResponseError(OpenAIServiceError):
    """Raised when OpenAI returns an empty or unparseable structured response."""


class InvalidExecutionPlanError(OpenAIServiceError):
    """Raised when the planner output lacks actionable clinical trial search criteria."""


class OpenAITimeoutError(OpenAIServiceError):
    """Raised when an OpenAI request times out."""


class ClinicalTrialsServiceError(AppError):
    """Raised when ClinicalTrials.gov integration fails."""


class ClinicalTrialsAPIError(ClinicalTrialsServiceError):
    """Raised when the ClinicalTrials.gov API returns an error response."""


class ClinicalTrialsTimeoutError(ClinicalTrialsServiceError):
    """Raised when a ClinicalTrials.gov request times out."""


class NoStudiesFoundError(ClinicalTrialsServiceError):
    """Raised when a search returns zero studies."""


class VisualizationServiceError(AppError):
    """Raised when visualization generation fails."""


class InvalidVisualizationError(VisualizationServiceError):
    """Raised when aggregated data cannot be rendered as a visualization."""
