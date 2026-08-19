from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete, select

from security_daily.application import (
    CollectDailyNews,
    DailyPipeline,
    SelectDailyNewsResult,
)
from security_daily.domain import PipelineStage
from security_daily.infrastructure.crawler.dto import CrawledArticle
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import ArticleModel, PipelineRunModel
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyArticleRepository,
    SQLAlchemyPipelineRunRepository,
)


KST = ZoneInfo("Asia/Seoul")


class FixedCrawler:
    def __init__(self, source_article_id: str) -> None:
        self._source_article_id = source_article_id

    def collect(self, target_date: object) -> list[CrawledArticle]:
        return [
            CrawledArticle(
                source_article_id=self._source_article_id,
                url=(
                    "https://www.boannews.com/media/view.asp?idx="
                    f"{self._source_article_id}"
                ),
                title="Daily Pipeline 통합 테스트",
                content="정제된 테스트 본문",
                published_at=datetime(2026, 8, 18, 12, 0, tzinfo=KST),
            )
        ]


class FailingCrawler:
    def collect(self, target_date: object) -> list[CrawledArticle]:
        raise RuntimeError("integration failure")


class FakeSelectorUseCase:
    def execute(self, target_date: object, selected_at: datetime) -> SelectDailyNewsResult:
        return SelectDailyNewsResult(
            target_date, 16, 3, "phi4-mini", 0.1  # type: ignore[arg-type]
        )


@pytest.mark.integration
def test_daily_pipeline_persists_success_and_prevents_duplicates_on_rerun() -> None:
    source_article_id = f"pipeline-test-{uuid4()}"
    run_at = datetime(2026, 8, 19, 8, 30, tzinfo=KST)
    session = get_session_factory()()
    run_ids: list[int] = []
    try:
        pipeline = DailyPipeline(
            CollectDailyNews(
                FixedCrawler(source_article_id),  # type: ignore[arg-type]
                SQLAlchemyArticleRepository(session),
            ),
            SQLAlchemyPipelineRunRepository(session),
            clock=lambda: run_at,
        )

        first = pipeline.execute(run_at)
        run_ids.append(first.run_id)
        second = pipeline.execute(run_at)
        run_ids.append(second.run_id)

        assert (first.collection.saved_count, first.collection.duplicate_count) == (1, 0)
        assert (second.collection.saved_count, second.collection.duplicate_count) == (0, 1)

        runs = session.scalars(
            select(PipelineRunModel)
            .where(PipelineRunModel.id.in_([first.run_id, second.run_id]))
            .order_by(PipelineRunModel.id)
        ).all()
        assert [run.status for run in runs] == ["SUCCESS", "SUCCESS"]
        assert [(run.saved_count, run.duplicate_count) for run in runs] == [
            (1, 0),
            (0, 1),
        ]
    finally:
        session.execute(
            delete(ArticleModel).where(
                ArticleModel.source_article_id == source_article_id
            )
        )
        if run_ids:
            session.execute(
                delete(PipelineRunModel).where(PipelineRunModel.id.in_(run_ids))
            )
        session.commit()
        session.close()


@pytest.mark.integration
def test_daily_pipeline_persists_failed_status() -> None:
    run_at = datetime(2026, 8, 19, 8, 30, tzinfo=KST)
    session = get_session_factory()()
    run_id: int | None = None
    try:
        pipeline = DailyPipeline(
            CollectDailyNews(
                FailingCrawler(),  # type: ignore[arg-type]
                SQLAlchemyArticleRepository(session),
            ),
            SQLAlchemyPipelineRunRepository(session),
            clock=lambda: run_at,
        )

        with pytest.raises(RuntimeError, match="integration failure"):
            pipeline.execute(run_at)

        failed_run = session.scalar(
            select(PipelineRunModel).order_by(PipelineRunModel.id.desc()).limit(1)
        )
        assert failed_run is not None
        run_id = failed_run.id
        assert failed_run.status == "FAILED"
        assert failed_run.error_type == "RuntimeError"
    finally:
        if run_id is not None:
            session.execute(
                delete(PipelineRunModel).where(PipelineRunModel.id == run_id)
            )
            session.commit()
        session.close()


@pytest.mark.integration
def test_daily_pipeline_persists_select_stage_counts_without_collecting() -> None:
    run_at = datetime(2026, 8, 19, 8, 30, tzinfo=KST)
    session = get_session_factory()()
    run_id: int | None = None
    try:
        pipeline = DailyPipeline(
            CollectDailyNews(
                FailingCrawler(),  # type: ignore[arg-type]
                SQLAlchemyArticleRepository(session),
            ),
            SQLAlchemyPipelineRunRepository(session),
            FakeSelectorUseCase(),  # type: ignore[arg-type]
            clock=lambda: run_at,
        )

        result = pipeline.execute(run_at, PipelineStage.SELECT)
        run_id = result.run_id
        persisted = session.get(PipelineRunModel, run_id)

        assert persisted is not None
        assert persisted.stage == "SELECT"
        assert persisted.status == "SUCCESS"
        assert persisted.candidate_count == 16
        assert persisted.selected_count == 3
        assert result.collection is None
    finally:
        if run_id is not None:
            session.execute(
                delete(PipelineRunModel).where(PipelineRunModel.id == run_id)
            )
            session.commit()
        session.close()
