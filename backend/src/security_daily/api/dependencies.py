from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from security_daily.application import GetNewsBriefing, GetQuizzes, GradeQuizAnswer
from security_daily.infrastructure.database import get_db_session
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyQuizAttemptRepository,
    SQLAlchemyQuizRepository,
    SQLAlchemyNewsQueryRepository,
)


DbSession = Annotated[Session, Depends(get_db_session)]


def get_quiz_query(session: DbSession) -> GetQuizzes:
    return GetQuizzes(SQLAlchemyQuizRepository(session))


def get_quiz_grader(session: DbSession) -> GradeQuizAnswer:
    return GradeQuizAnswer(
        SQLAlchemyQuizRepository(session), SQLAlchemyQuizAttemptRepository(session)
    )


def get_news_query(session: DbSession) -> GetNewsBriefing:
    return GetNewsBriefing(SQLAlchemyNewsQueryRepository(session))
