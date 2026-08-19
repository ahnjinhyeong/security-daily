from datetime import date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import delete, select

from security_daily.application import GradeQuizAnswer
from security_daily.domain import Article, Quiz
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.models import ArticleModel, QuizAttemptModel, QuizModel
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyArticleRepository,
    SQLAlchemyQuizAttemptRepository,
    SQLAlchemyQuizRepository,
)


@pytest.mark.integration
def test_grade_quiz_answer_stores_postgresql_attempt() -> None:
    session = get_session_factory()()
    token = str(uuid4())
    quiz_date = date(2099, 3, 1)
    now = datetime(2099, 3, 2, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    article_id: int | None = None
    quiz_id: int | None = None
    try:
        article = SQLAlchemyArticleRepository(session).add(
            Article("attempt-test", token, "기사", f"https://example.test/{token}", "본문", now, now)
        )
        assert article.id is not None
        article_id = article.id
        quiz = SQLAlchemyQuizRepository(session).save_for_date(
            quiz_date,
            [Quiz(article.id, quiz_date, "약어?", "RCE", ["Remote Code Execution"], "해설", "test")],
        )[0]
        assert quiz.id is not None
        quiz_id = quiz.id

        result = GradeQuizAnswer(
            SQLAlchemyQuizRepository(session), SQLAlchemyQuizAttemptRepository(session)
        ).execute(quiz.id, " remote   code execution ")

        stored = session.scalar(select(QuizAttemptModel).where(QuizAttemptModel.quiz_id == quiz.id))
        assert result.correct is True
        assert stored is not None
        assert stored.user_answer == " remote   code execution "
        assert stored.is_correct is True
    finally:
        if quiz_id is not None:
            session.execute(delete(QuizAttemptModel).where(QuizAttemptModel.quiz_id == quiz_id))
            session.execute(delete(QuizModel).where(QuizModel.id == quiz_id))
        if article_id is not None:
            session.execute(delete(ArticleModel).where(ArticleModel.id == article_id))
        session.commit()
        session.close()
