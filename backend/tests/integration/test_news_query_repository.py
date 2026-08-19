from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete

from security_daily.domain import Article, DailySelection
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import (
    AiAnalysisModel,
    ArticleModel,
    DailySelectionModel,
)
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyAiAnalysisRepository,
    SQLAlchemyArticleRepository,
    SQLAlchemyDailySelectionRepository,
    SQLAlchemyNewsQueryRepository,
)


@pytest.mark.integration
def test_news_query_joins_only_selections_with_analysis_and_counts_dates() -> None:
    session = get_session_factory()()
    token = str(uuid4())
    target_date = date(2099, 4, 1)
    now = datetime(2099, 4, 2, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    article_ids: list[int] = []
    try:
        article_repository = SQLAlchemyArticleRepository(session)
        selected = article_repository.add(
            Article("news-api-test", token + "-1", "선정", f"https://example.test/{token}/1", "본문", now, now)
        )
        unselected = article_repository.add(
            Article("news-api-test", token + "-2", "미선정", f"https://example.test/{token}/2", "본문", now, now)
        )
        assert selected.id is not None and unselected.id is not None
        article_ids.extend([selected.id, unselected.id])
        SQLAlchemyDailySelectionRepository(session).replace_for_date(
            target_date,
            [DailySelection(selected.id, target_date, 1, Decimal("90"), "이유", "test")],
        )
        analysis_repository = SQLAlchemyAiAnalysisRepository(session)
        analysis_repository.save_summary(selected.id, "통합 요약", "test", now)
        analysis_repository.save_analysis(
            selected.id, "중요", "공격", ["조치"], [{"name": "개념", "description": "설명"}], [], "test", now
        )

        repository = SQLAlchemyNewsQueryRepository(session)
        results = repository.list_for_date(target_date)
        dates = repository.list_available_dates()

        assert [item.article_id for item in results] == [selected.id]
        assert results[0].summary == "통합 요약"
        assert results[0].importance == "중요"
        date_result = next(item for item in dates if item.date == target_date)
        assert date_result.article_count == 1
    finally:
        session.execute(delete(AiAnalysisModel).where(AiAnalysisModel.article_id.in_(article_ids)))
        session.execute(delete(DailySelectionModel).where(DailySelectionModel.selection_date == target_date))
        session.execute(delete(ArticleModel).where(ArticleModel.id.in_(article_ids)))
        session.commit()
        session.close()
