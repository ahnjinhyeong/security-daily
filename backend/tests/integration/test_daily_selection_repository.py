from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete

from security_daily.domain import Article, DailySelection
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import ArticleModel, DailySelectionModel
from security_daily.infrastructure.database.repositories import (
    DailySelectionConstraintError,
    SQLAlchemyArticleRepository,
    SQLAlchemyDailySelectionRepository,
)


KST = ZoneInfo("Asia/Seoul")
TARGET_DATE = date(2099, 1, 1)
NOW = datetime(2026, 8, 19, 8, 30, tzinfo=KST)


@pytest.mark.integration
def test_daily_selection_repository_replaces_and_lists_results() -> None:
    token = str(uuid4())
    session = get_session_factory()()
    article_ids: list[int] = []
    try:
        article_repository = SQLAlchemyArticleRepository(session)
        for rank in (1, 2):
            saved = article_repository.add(
                Article(
                    source="selector-test",
                    source_article_id=f"{token}-{rank}",
                    title=f"선정 테스트 기사 {rank}",
                    url=f"https://example.test/{token}/{rank}",
                    content="정제 본문",
                    published_at=datetime(2099, 1, 1, 12, rank, tzinfo=KST),
                    collected_at=NOW,
                )
            )
            assert saved.id is not None
            article_ids.append(saved.id)

        repository = SQLAlchemyDailySelectionRepository(session)
        repository.replace_for_date(
            TARGET_DATE,
            [
                DailySelection(
                    article_id=article_id,
                    selection_date=TARGET_DATE,
                    rank=rank,
                    score=Decimal("90.00") - rank,
                    reason="통합 테스트 선정",
                    model_name="phi4-mini",
                    created_at=NOW,
                )
                for rank, article_id in enumerate(article_ids, start=1)
            ],
        )

        listed = repository.list_for_date(TARGET_DATE)
        assert [item.article_id for item in listed] == article_ids
        assert [item.rank for item in listed] == [1, 2]

        repository.replace_for_date(
            TARGET_DATE,
            [
                DailySelection(
                    article_id=article_ids[1],
                    selection_date=TARGET_DATE,
                    rank=1,
                    score=Decimal("75.00"),
                    reason="재실행 교체",
                    model_name="phi4-mini",
                    created_at=NOW,
                )
            ],
        )
        replaced = repository.list_for_date(TARGET_DATE)
        assert len(replaced) == 1
        assert replaced[0].article_id == article_ids[1]
    finally:
        session.execute(
            delete(DailySelectionModel).where(
                DailySelectionModel.selection_date == TARGET_DATE
            )
        )
        if article_ids:
            session.execute(delete(ArticleModel).where(ArticleModel.id.in_(article_ids)))
        session.commit()
        session.close()


@pytest.mark.integration
def test_daily_selection_repository_enforces_article_fk() -> None:
    session = get_session_factory()()
    repository = SQLAlchemyDailySelectionRepository(session)
    try:
        with pytest.raises(DailySelectionConstraintError):
            repository.replace_for_date(
                TARGET_DATE,
                [
                    DailySelection(
                        article_id=9_999_999_999,
                        selection_date=TARGET_DATE,
                        rank=1,
                        score=Decimal("80"),
                        reason="존재하지 않는 기사",
                        model_name="phi4-mini",
                        created_at=NOW,
                    )
                ],
            )
    finally:
        session.rollback()
        session.close()
