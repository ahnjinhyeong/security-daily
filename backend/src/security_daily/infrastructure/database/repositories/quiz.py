from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from security_daily.domain import Quiz
from security_daily.infrastructure.database.models import QuizModel


class SQLAlchemyQuizRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_date(self, quiz_date: date) -> list[Quiz]:
        models = self._session.scalars(
            select(QuizModel).where(QuizModel.quiz_date == quiz_date).order_by(QuizModel.id)
        ).all()
        return [self._to_domain(model) for model in models]

    def save_for_date(self, quiz_date: date, quizzes: list[Quiz]) -> list[Quiz]:
        models = [
            QuizModel(
                article_id=quiz.article_id,
                quiz_date=quiz_date,
                question=quiz.question,
                answer=quiz.answer,
                accepted_answers=quiz.accepted_answers,
                explanation=quiz.explanation,
                model_name=quiz.model_name,
                created_at=quiz.created_at,
            )
            for quiz in quizzes
        ]
        self._session.add_all(models)
        try:
            self._session.commit()
            for model in models:
                self._session.refresh(model)
        except SQLAlchemyError:
            self._session.rollback()
            raise
        return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: QuizModel) -> Quiz:
        return Quiz(
            id=model.id,
            article_id=model.article_id,
            quiz_date=model.quiz_date,
            question=model.question,
            answer=model.answer,
            accepted_answers=model.accepted_answers,
            explanation=model.explanation,
            model_name=model.model_name,
            created_at=model.created_at,
        )
    def get_by_id(self, quiz_id: int) -> Quiz | None:
        model = self._session.get(QuizModel, quiz_id)
        return self._to_domain(model) if model is not None else None
