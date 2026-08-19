from datetime import date, datetime

from security_daily.domain import PipelineStage
from security_daily.jobs import daily


def test_daily_job_cli_runs_requested_target_date(monkeypatch: object) -> None:
    received: list[datetime | None] = []

    def fake_run_daily_job(run_at: datetime | None = None, start_stage: object = None) -> object:
        received.append(run_at)
        return object()

    monkeypatch.setattr(daily, "run_daily_job", fake_run_daily_job)  # type: ignore[attr-defined]

    assert daily.main(["--target-date", "2026-08-18"]) == 0
    assert received[0] is not None
    assert received[0].date() == date(2026, 8, 19)
    assert received[0].hour == 8
    assert received[0].minute == 30
    assert received[0].utcoffset() is not None


def test_daily_job_cli_returns_failure_exit_code(monkeypatch: object) -> None:
    def fail(run_at: datetime | None = None, start_stage: object = None) -> object:
        raise RuntimeError("failed")

    monkeypatch.setattr(daily, "run_daily_job", fail)  # type: ignore[attr-defined]

    assert daily.main([]) == 1


def test_daily_job_cli_can_restart_from_select(monkeypatch: object) -> None:
    received: list[PipelineStage] = []

    def fake_run_daily_job(
        run_at: datetime | None = None,
        start_stage: PipelineStage = PipelineStage.COLLECT,
    ) -> object:
        received.append(start_stage)
        return object()

    monkeypatch.setattr(daily, "run_daily_job", fake_run_daily_job)  # type: ignore[attr-defined]

    assert daily.main(["--start-stage", "SELECT"]) == 0
    assert received == [PipelineStage.SELECT]
