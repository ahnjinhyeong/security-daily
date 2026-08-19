from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from security_daily.domain import QuizAttempt
from security_daily.infrastructure.database.models import QuizAttemptModel


class SQLAlchemyQuizAttemptRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, attempt: QuizAttempt) -> QuizAttempt:
        model = QuizAttemptModel(
            quiz_id=attempt.quiz_id,
            user_answer=attempt.user_answer,
            is_correct=attempt.is_correct,
            answered_at=attempt.answered_at,
        )
        self._session.add(model)
        try:
            self._session.commit()
            self._session.refresh(model)
        except SQLAlchemyError:
            self._session.rollback()
            raise
        return QuizAttempt(
            id=model.id,
            quiz_id=model.quiz_id,
            user_answer=model.user_answer,
            is_correct=model.is_correct,
            answered_at=model.answered_at,
        )
