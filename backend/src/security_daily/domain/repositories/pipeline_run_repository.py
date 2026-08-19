from datetime import date, datetime
from typing import Protocol

from security_daily.domain.pipeline_run import PipelineRun, PipelineStage


class PipelineRunRepository(Protocol):
    def create_pending(
        self, target_date: date, stage: PipelineStage, created_at: datetime
    ) -> PipelineRun: ...

    def mark_running(self, run_id: int, started_at: datetime) -> None: ...

    def mark_success(
        self,
        run_id: int,
        finished_at: datetime,
        crawled_count: int,
        saved_count: int,
        duplicate_count: int,
        candidate_count: int = 0,
        selected_count: int = 0,
    ) -> None: ...

    def mark_failed(
        self, run_id: int, finished_at: datetime, error_type: str
    ) -> None: ...
