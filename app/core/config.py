"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = Field(..., min_length=1, description="OpenAI API key")
    clinical_trials_base_url: HttpUrl = Field(
        default="https://clinicaltrials.gov/api/v2",
        description="ClinicalTrials.gov API v2 base URL",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="HTTP client timeout in seconds",
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model used for intent extraction",
    )
    log_level: str = Field(default="INFO", description="Application log level")
    clinical_trials_page_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size for ClinicalTrials.gov study searches",
    )
    clinical_trials_max_pages: int = Field(
        default=50,
        ge=1,
        description="Maximum number of pages to fetch per search",
    )

    @property
    def clinical_trials_base_url_str(self) -> str:
        """Return the ClinicalTrials.gov base URL as a plain string."""
        return str(self.clinical_trials_base_url).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
