from datetime import date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from security_daily.domain import Article, Quiz
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import ArticleModel, QuizModel
from security_daily.infrastructure.database.repositories import SQLAlchemyArticleRepository, SQLAlchemyQuizRepository


@pytest.mark.integration
def test_quiz_repository_stores_jsonb_and_enforces_fk() -> None:
    session = get_session_factory()()
    token = str(uuid4())
    article_id: int | None = None
    quiz_date = date(2099, 2, 1)
    now = datetime(2099, 2, 2, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    try:
        article = SQLAlchemyArticleRepository(session).add(
            Article("quiz-test", token, "퀴즈 기사", f"https://example.test/{token}", "본문", now, now)
        )
        assert article.id is not None
        article_id = article.id
        repository = SQLAlchemyQuizRepository(session)
        repository.save_for_date(
            quiz_date,
            [Quiz(article_id, quiz_date, "RCE란?", "원격 코드 실행", ["RCE"], "해설", "llama3.2:3b", created_at=now)],
        )
        listed = repository.list_for_date(quiz_date)
        assert listed[0].accepted_answers == ["RCE"]

        session.add(QuizModel(article_id=9_999_999_999, quiz_date=quiz_date, question="FK?", answer="답", accepted_answers=[], explanation="해설", model_name="test"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.execute(delete(QuizModel).where(QuizModel.quiz_date == quiz_date))
        if article_id is not None:
            session.execute(delete(ArticleModel).where(ArticleModel.id == article_id))
        session.commit()
        session.close()
