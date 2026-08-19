import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from security_daily.application import (
    CollectDailyNewsResult,
    DailyPipeline,
    SelectDailyNewsResult,
)
from security_daily.domain import PipelineRun, PipelineStage, PipelineStatus


KST = ZoneInfo("Asia/Seoul")
RUN_AT = datetime(2026, 8, 19, 8, 30, tzinfo=KST)


class FakeCollector:
    def execute(self, run_at: datetime) -> CollectDailyNewsResult:
        return CollectDailyNewsResult(date(2026, 8, 18), 3, 2, 1)


class FailingCollector:
    def execute(self, run_at: datetime) -> CollectDailyNewsResult:
        raise RuntimeError("기사 원문을 로그에 남기지 않는다")


class CountingCollector(FakeCollector):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, run_at: datetime) -> CollectDailyNewsResult:
        self.calls += 1
        return super().execute(run_at)


class FakeSelectorUseCase:
    def execute(self, target_date: date, selected_at: datetime) -> SelectDailyNewsResult:
        return SelectDailyNewsResult(target_date, 3, 2, "phi4-mini", 0.5)


class FailingSelectorUseCase:
    def execute(self, target_date: date, selected_at: datetime) -> SelectDailyNewsResult:
        raise RuntimeError("selector failed")


class FakeRunRepository:
    def __init__(self) -> None:
        self.transitions: list[tuple[object, ...]] = []
        self.next_id = 7

    def create_pending(
        self, target_date: date, stage: PipelineStage, created_at: datetime
    ) -> PipelineRun:
        self.transitions.append((PipelineStatus.PENDING, target_date, stage))
        run_id = self.next_id
        self.next_id += 1
        return PipelineRun(target_date, stage, PipelineStatus.PENDING, id=run_id)

    def mark_running(self, run_id: int, started_at: datetime) -> None:
        self.transitions.append((PipelineStatus.RUNNING, run_id))

    def mark_success(
        self,
        run_id: int,
        finished_at: datetime,
        crawled_count: int,
        saved_count: int,
        duplicate_count: int,
        candidate_count: int = 0,
        selected_count: int = 0,
    ) -> None:
        self.transitions.append(
            (
                PipelineStatus.SUCCESS,
                run_id,
                crawled_count,
                saved_count,
                duplicate_count,
                candidate_count,
                selected_count,
            )
        )

    def mark_failed(
        self, run_id: int, finished_at: datetime, error_type: str
    ) -> None:
        self.transitions.append((PipelineStatus.FAILED, run_id, error_type))


def test_daily_pipeline_records_success_and_collection_counts(
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = FakeRunRepository()
    timer_values = iter((10.0, 10.0, 12.5, 12.5))
    pipeline = DailyPipeline(
        FakeCollector(),  # type: ignore[arg-type]
        repository,
        clock=lambda: RUN_AT,
        timer=lambda: next(timer_values),
    )

    with caplog.at_level(logging.INFO):
        result = pipeline.execute(RUN_AT)

    assert result.run_id == 7
    assert result.elapsed_seconds == 2.5
    assert repository.transitions == [
        (PipelineStatus.PENDING, date(2026, 8, 18), PipelineStage.COLLECT),
        (PipelineStatus.RUNNING, 7),
        (PipelineStatus.SUCCESS, 7, 3, 2, 1, 0, 0),
    ]
    assert "target_date=2026-08-18" in caplog.text
    assert "crawled_count=3 saved_count=2 duplicate_count=1" in caplog.text


def test_daily_pipeline_records_failure_without_logging_error_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = FakeRunRepository()
    pipeline = DailyPipeline(
        FailingCollector(),  # type: ignore[arg-type]
        repository,
        clock=lambda: RUN_AT,
        timer=lambda: 1.0,
    )

    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
        pipeline.execute(RUN_AT)

    assert repository.transitions[-1] == (PipelineStatus.FAILED, 7, "RuntimeError")
    assert "stage=COLLECT error_type=RuntimeError" in caplog.text
    assert "기사 원문" not in caplog.text


def test_daily_pipeline_can_restart_from_select_without_collecting() -> None:
    collector = CountingCollector()
    repository = FakeRunRepository()
    pipeline = DailyPipeline(
        collector,  # type: ignore[arg-type]
        repository,
        FakeSelectorUseCase(),  # type: ignore[arg-type]
        clock=lambda: RUN_AT,
        timer=lambda: 1.0,
    )

    result = pipeline.execute(RUN_AT, PipelineStage.SELECT)

    assert collector.calls == 0
    assert result.collection is None
    assert result.selection is not None
    assert result.selection.selected_count == 2
    assert repository.transitions == [
        (PipelineStatus.PENDING, date(2026, 8, 18), PipelineStage.SELECT),
        (PipelineStatus.RUNNING, 7),
        (PipelineStatus.SUCCESS, 7, 0, 0, 0, 3, 2),
    ]


def test_selector_failure_marks_select_failed_after_collect_success() -> None:
    repository = FakeRunRepository()
    pipeline = DailyPipeline(
        FakeCollector(),  # type: ignore[arg-type]
        repository,
        FailingSelectorUseCase(),  # type: ignore[arg-type]
        clock=lambda: RUN_AT,
        timer=lambda: 1.0,
    )

    with pytest.raises(RuntimeError, match="selector failed"):
        pipeline.execute(RUN_AT)

    assert (PipelineStatus.SUCCESS, 7, 3, 2, 1, 0, 0) in repository.transitions
    assert repository.transitions[-1] == (PipelineStatus.FAILED, 8, "RuntimeError")
