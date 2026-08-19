from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from security_daily.domain import DailySelection
from security_daily.infrastructure.database.models import DailySelectionModel


class DailySelectionConstraintError(Exception):
    """선정 결과가 FK 또는 날짜별 UNIQUE 제약을 위반했다."""


class SQLAlchemyDailySelectionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_date(
        self, selection_date: date, selections: list[DailySelection]
    ) -> list[DailySelection]:
        try:
            self._session.execute(
                delete(DailySelectionModel).where(
                    DailySelectionModel.selection_date == selection_date
                )
            )
            models = [self._to_model(selection) for selection in selections]
            self._session.add_all(models)
            self._session.commit()
            for model in models:
                self._session.refresh(model)
        except IntegrityError as error:
            self._session.rollback()
            raise DailySelectionConstraintError(
                "Daily selection constraints were violated"
            ) from error
        return [self._to_domain(model) for model in models]

    def list_for_date(self, selection_date: date) -> list[DailySelection]:
        statement = (
            select(DailySelectionModel)
            .where(DailySelectionModel.selection_date == selection_date)
            .order_by(DailySelectionModel.rank)
        )
        return [self._to_domain(model) for model in self._session.scalars(statement)]

    @staticmethod
    def _to_model(selection: DailySelection) -> DailySelectionModel:
        return DailySelectionModel(
            article_id=selection.article_id,
            selection_date=selection.selection_date,
            rank=selection.rank,
            score=selection.score,
            reason=selection.reason,
            model_name=selection.model_name,
            created_at=selection.created_at,
        )

    @staticmethod
    def _to_domain(model: DailySelectionModel) -> DailySelection:
        return DailySelection(
            id=model.id,
            article_id=model.article_id,
            selection_date=model.selection_date,
            rank=model.rank,
            score=model.score,
            reason=model.reason,
            model_name=model.model_name,
            created_at=model.created_at,
        )

