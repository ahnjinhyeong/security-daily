from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# 소스 위치를 기준으로 저장소 루트의 .env를 찾으므로 실행 디렉터리에 의존하지 않는다.
PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    database_url: str = Field(min_length=1)
    ollama_base_url: str = Field(default="http://localhost:11434", min_length=1)
    selector_model: str = Field(default="phi4-mini", min_length=1)
    ollama_timeout_seconds: float = Field(default=120.0, gt=0)
    selector_max_content_chars: int = Field(default=3000, ge=500)
    selector_max_total_content_chars: int = Field(default=24000, ge=1000)
    summary_model: str = Field(default="gemma3:4b", min_length=1)
    analyst_model: str = Field(default="qwen3.5:9b", min_length=1)
    quiz_model: str = Field(default="llama3.2:3b", min_length=1)
    analysis_max_content_chars: int = Field(default=12000, ge=1000)
    boannews_base_url: str = "https://www.boannews.com"
    crawler_timeout_seconds: float = Field(default=20.0, gt=0)
    crawler_max_retries: int = Field(default=2, ge=0, le=5)
    crawler_max_pages: int = Field(default=100, ge=1)
    crawler_user_agent: str = "SecurityDaily/0.1 (+personal security learning)"

    @field_validator(
        "ollama_base_url", "selector_model", "summary_model", "analyst_model", "quiz_model", mode="before"
    )
    @classmethod
    def use_architecture_defaults_for_blank_values(
        cls, value: object, info: ValidationInfo
    ) -> object:
        if isinstance(value, str) and not value.strip():
            return {
                "ollama_base_url": "http://localhost:11434",
                "selector_model": "phi4-mini",
                "summary_model": "gemma3:4b",
                "analyst_model": "qwen3.5:9b",
                "quiz_model": "llama3.2:3b",
            }[info.field_name]
        return value

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the validated process-wide application settings."""
    return Settings()  # type: ignore[call-arg]
