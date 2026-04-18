"""Configuration management for AI Visibility."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    providers: str = "openai,anthropic"
    db_path: str = "./data/ai_visibility.db"
    log_level: str = "INFO"
    llm_framework: str = "solaraai-llm"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def providers_list(self) -> List[str]:
        """Parse comma-separated providers into a list."""
        return [p.strip() for p in self.providers.split(",") if p.strip()]


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
