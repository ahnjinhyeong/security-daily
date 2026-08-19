from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class PipelineStage(StrEnum):
    COLLECT = "COLLECT"
    SELECT = "SELECT"
    SUMMARY = "SUMMARY"
    ANALYZE = "ANALYZE"
    QUIZ = "QUIZ"


class PipelineStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PipelineRun:
    target_date: date
    stage: PipelineStage
    status: PipelineStatus
    id: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    crawled_count: int = 0
    saved_count: int = 0
    duplicate_count: int = 0
    candidate_count: int = 0
    selected_count: int = 0
    error_type: str | None = None
