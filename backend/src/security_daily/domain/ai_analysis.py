from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class AnalysisStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class AiAnalysis:
    article_id: int
    summary_status: AnalysisStatus
    analyst_status: AnalysisStatus
    id: int | None = None
    summary: str | None = None
    importance: str | None = None
    attack_scenario: str | None = None
    security_actions: list[str] | None = None
    key_concepts: list[dict[str, str]] | None = None
    related_security_info: list[dict[str, str]] | None = None
    summary_model: str | None = None
    analyst_model: str | None = None
    error_type: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
