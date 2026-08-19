from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from security_daily.domain import AnalysisStatus, Article
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import AiAnalysisModel, ArticleModel
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyAiAnalysisRepository,
    SQLAlchemyArticleRepository,
)


@pytest.mark.integration
def test_ai_analysis_repository_stores_jsonb_and_enforces_unique_article() -> None:
    session = get_session_factory()()
    token = str(uuid4())
    article_id: int | None = None
    now = datetime(2026, 8, 20, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    try:
        saved = SQLAlchemyArticleRepository(session).add(
            Article("analysis-test", token, "분석 기사", f"https://example.test/{token}", "본문", now, now)
        )
        assert saved.id is not None
        article_id = saved.id
        repository = SQLAlchemyAiAnalysisRepository(session)
        repository.mark_summary_running(article_id, now)
        repository.save_summary(article_id, "사실 요약.", "gemma3:4b", now)
        repository.mark_analyst_running(article_id, now)
        repository.save_analysis(
            article_id,
            "중요성",
            "POSSIBLE: 공격 시나리오",
            ["패치 확인"],
            [{"name": "RCE", "description": "원격 코드 실행"}],
            [{"type": "VULNERABILITY", "value": "RCE"}],
            "qwen3.5:9b",
            now,
        )
        analysis = repository.get_by_article_id(article_id)
        assert analysis is not None
        assert analysis.summary_status is AnalysisStatus.SUCCESS
        assert analysis.analyst_status is AnalysisStatus.SUCCESS
        assert analysis.key_concepts == [{"name": "RCE", "description": "원격 코드 실행"}]

        session.add(AiAnalysisModel(article_id=article_id, summary_status="PENDING", analyst_status="PENDING"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        if article_id is not None:
            session.execute(delete(AiAnalysisModel).where(AiAnalysisModel.article_id == article_id))
            session.execute(delete(ArticleModel).where(ArticleModel.id == article_id))
            session.commit()
        session.close()


@pytest.mark.integration
def test_ai_analysis_enforces_article_fk() -> None:
    session = get_session_factory()()
    try:
        session.add(AiAnalysisModel(article_id=9_999_999_999, summary_status="PENDING", analyst_status="PENDING"))
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()
