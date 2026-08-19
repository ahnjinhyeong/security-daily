from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete, inspect

from security_daily.domain import Article
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import ArticleModel
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyArticleRepository,
)


KST = ZoneInfo("Asia/Seoul")


@pytest.mark.integration
def test_articles_schema_has_required_identity_constraints() -> None:
    session = get_session_factory()()
    try:
        inspector = inspect(session.get_bind())
        constraints = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints("articles")
        }
        indexes = {
            tuple(index["column_names"])
            for index in inspector.get_indexes("articles")
        }

        assert ("url",) in constraints
        assert ("source", "source_article_id") in constraints
        assert ("published_at",) in indexes
    finally:
        session.close()


@pytest.mark.integration
def test_article_repository_saves_and_finds_article() -> None:
    source_article_id = f"test-{uuid4()}"
    url = f"https://www.boannews.com/media/view.asp?idx={source_article_id}"
    session = get_session_factory()()
    repository = SQLAlchemyArticleRepository(session)
    try:
        saved = repository.add(
            Article(
                source="boannews-test",
                source_article_id=source_article_id,
                title="Repository 테스트 기사",
                url=url,
                content="정제된 테스트 본문",
                published_at=datetime(2026, 8, 18, 12, 0, tzinfo=KST),
                collected_at=datetime(2026, 8, 19, 8, 30, tzinfo=KST),
            )
        )

        assert saved.id is not None
        assert repository.exists_by_source_id("boannews-test", source_article_id)
    finally:
        session.execute(delete(ArticleModel).where(ArticleModel.url == url))
        session.commit()
        session.close()
