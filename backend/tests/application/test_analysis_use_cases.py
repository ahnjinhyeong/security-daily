from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from security_daily.agents.summary.schemas import SummaryOutput
from security_daily.application import SummarizeArticle
from security_daily.domain import AiAnalysis, AnalysisStatus, Article


NOW = datetime(2026, 8, 20, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))


class FailingSummaryAgent:
    model_name = "gemma3:4b"
    def summarize(self, article: Article) -> SummaryOutput:
        raise RuntimeError("llm failed")


class FakeAnalysisRepository:
    def __init__(self, existing: AiAnalysis | None = None) -> None:
        self.existing = existing
        self.transitions: list[str] = []
    def get_by_article_id(self, article_id: int) -> AiAnalysis | None:
        return self.existing
    def mark_summary_running(self, article_id: int, at: datetime) -> None:
        self.transitions.append("RUNNING")
    def mark_summary_failed(self, article_id: int, error_type: str, at: datetime) -> None:
        self.transitions.append(f"FAILED:{error_type}")


def article() -> Article:
    return Article("test", "1", "기사", "https://example.test/1", "본문", NOW, NOW, id=1)


def test_summary_failure_records_failed_status() -> None:
    repository = FakeAnalysisRepository()
    with pytest.raises(RuntimeError):
        SummarizeArticle(FailingSummaryAgent(), repository).execute(article(), NOW)  # type: ignore[arg-type]
    assert repository.transitions == ["RUNNING", "FAILED:RuntimeError"]


def test_successful_summary_is_skipped_on_rerun() -> None:
    repository = FakeAnalysisRepository(
        AiAnalysis(1, AnalysisStatus.SUCCESS, AnalysisStatus.PENDING, summary="기존 요약")
    )
    result = SummarizeArticle(FailingSummaryAgent(), repository).execute(article(), NOW)  # type: ignore[arg-type]
    assert result.skipped is True
    assert repository.transitions == []
