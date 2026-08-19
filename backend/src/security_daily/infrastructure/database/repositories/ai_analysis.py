from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from security_daily.domain import AiAnalysis, AnalysisStatus
from security_daily.infrastructure.database.models import AiAnalysisModel


class SQLAlchemyAiAnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_article_id(self, article_id: int) -> AiAnalysis | None:
        model = self._session.scalar(
            select(AiAnalysisModel).where(AiAnalysisModel.article_id == article_id)
        )
        return self._to_domain(model) if model else None

    def mark_summary_running(self, article_id: int, at: datetime) -> None:
        model = self._get_or_create(article_id, at)
        model.summary_status = AnalysisStatus.RUNNING.value
        model.error_type = None
        model.updated_at = at
        self._commit()

    def save_summary(
        self, article_id: int, summary: str, model_name: str, at: datetime
    ) -> None:
        model = self._get_or_create(article_id, at)
        model.summary = summary
        model.summary_model = model_name
        model.summary_status = AnalysisStatus.SUCCESS.value
        model.analyst_status = AnalysisStatus.PENDING.value
        model.error_type = None
        model.updated_at = at
        self._commit()

    def mark_summary_failed(
        self, article_id: int, error_type: str, at: datetime
    ) -> None:
        model = self._get_or_create(article_id, at)
        model.summary_status = AnalysisStatus.FAILED.value
        model.error_type = error_type
        model.updated_at = at
        self._commit()

    def mark_analyst_running(self, article_id: int, at: datetime) -> None:
        model = self._get_or_create(article_id, at)
        model.analyst_status = AnalysisStatus.RUNNING.value
        model.error_type = None
        model.updated_at = at
        self._commit()

    def save_analysis(
        self,
        article_id: int,
        importance: str,
        attack_scenario: str,
        security_actions: list[str],
        key_concepts: list[dict[str, str]],
        related_security_info: list[dict[str, str]],
        model_name: str,
        at: datetime,
    ) -> None:
        model = self._get_or_create(article_id, at)
        model.importance = importance
        model.attack_scenario = attack_scenario
        model.security_actions = security_actions
        model.key_concepts = key_concepts
        model.related_security_info = related_security_info
        model.analyst_model = model_name
        model.analyst_status = AnalysisStatus.SUCCESS.value
        model.error_type = None
        model.updated_at = at
        self._commit()

    def mark_analyst_failed(
        self, article_id: int, error_type: str, at: datetime
    ) -> None:
        model = self._get_or_create(article_id, at)
        model.analyst_status = AnalysisStatus.FAILED.value
        model.error_type = error_type
        model.updated_at = at
        self._commit()

    def _get_or_create(self, article_id: int, at: datetime) -> AiAnalysisModel:
        model = self._session.scalar(
            select(AiAnalysisModel).where(AiAnalysisModel.article_id == article_id)
        )
        if model is None:
            model = AiAnalysisModel(
                article_id=article_id,
                summary_status=AnalysisStatus.PENDING.value,
                analyst_status=AnalysisStatus.PENDING.value,
                created_at=at,
                updated_at=at,
            )
            self._session.add(model)
        return model

    def _commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    @staticmethod
    def _to_domain(model: AiAnalysisModel) -> AiAnalysis:
        return AiAnalysis(
            id=model.id,
            article_id=model.article_id,
            summary=model.summary,
            importance=model.importance,
            attack_scenario=model.attack_scenario,
            security_actions=model.security_actions,
            key_concepts=model.key_concepts,
            related_security_info=model.related_security_info,
            summary_model=model.summary_model,
            analyst_model=model.analyst_model,
            summary_status=AnalysisStatus(model.summary_status),
            analyst_status=AnalysisStatus(model.analyst_status),
            error_type=model.error_type,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
