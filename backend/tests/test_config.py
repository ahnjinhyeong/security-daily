from pathlib import Path

import pytest
from pydantic import ValidationError

from security_daily.config.settings import Settings


def test_settings_loads_database_url_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = "postgresql+psycopg://user:password@db:5432/security_daily"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings(_env_file=None)

    assert settings.database_url == database_url


def test_settings_loads_database_url_from_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+psycopg://user:password@db/security_daily\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.database_url.endswith("@db/security_daily")


def test_settings_rejects_missing_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_blank_ollama_values_use_architecture_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@db/test")
    monkeypatch.setenv("OLLAMA_BASE_URL", "")
    monkeypatch.setenv("SELECTOR_MODEL", "")
    monkeypatch.setenv("SUMMARY_MODEL", "")
    monkeypatch.setenv("ANALYST_MODEL", "")
    monkeypatch.setenv("QUIZ_MODEL", "")

    settings = Settings(_env_file=None)

    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.selector_model == "phi4-mini"
    assert settings.summary_model == "gemma3:4b"
    assert settings.analyst_model == "qwen3.5:9b"
    assert settings.quiz_model == "llama3.2:3b"
