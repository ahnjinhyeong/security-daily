from datetime import date, datetime

from sqlalchemy.orm import Session

from security_daily.domain import PipelineRun, PipelineStage, PipelineStatus
from security_daily.infrastructure.database.models import PipelineRunModel


class SQLAlchemyPipelineRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_pending(
        self, target_date: date, stage: PipelineStage, created_at: datetime
    ) -> PipelineRun:
        model = PipelineRunModel(
            target_date=target_date,
            stage=stage.value,
            status=PipelineStatus.PENDING.value,
            created_at=created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def mark_running(self, run_id: int, started_at: datetime) -> None:
        model = self._get(run_id)
        model.status = PipelineStatus.RUNNING.value
        model.started_at = started_at
        self._session.commit()

    def mark_success(
        self,
        run_id: int,
        finished_at: datetime,
        crawled_count: int,
        saved_count: int,
        duplicate_count: int,
        candidate_count: int = 0,
        selected_count: int = 0,
    ) -> None:
        model = self._get(run_id)
        model.status = PipelineStatus.SUCCESS.value
        model.finished_at = finished_at
        model.crawled_count = crawled_count
        model.saved_count = saved_count
        model.duplicate_count = duplicate_count
        model.candidate_count = candidate_count
        model.selected_count = selected_count
        model.error_type = None
        self._session.commit()

    def mark_failed(
        self, run_id: int, finished_at: datetime, error_type: str
    ) -> None:
        # 실패 원문 대신 예외 형식만 저장하여 Secret 노출 가능성을 줄인다.
        model = self._get(run_id)
        model.status = PipelineStatus.FAILED.value
        model.finished_at = finished_at
        model.error_type = error_type
        self._session.commit()

    def _get(self, run_id: int) -> PipelineRunModel:
        model = self._session.get(PipelineRunModel, run_id)
        if model is None:
            raise LookupError(f"Pipeline run not found: {run_id}")
        return model

    @staticmethod
    def _to_domain(model: PipelineRunModel) -> PipelineRun:
        return PipelineRun(
            id=model.id,
            target_date=model.target_date,
            stage=PipelineStage(model.stage),
            status=PipelineStatus(model.status),
            started_at=model.started_at,
            finished_at=model.finished_at,
            crawled_count=model.crawled_count,
            saved_count=model.saved_count,
            duplicate_count=model.duplicate_count,
            candidate_count=model.candidate_count,
            selected_count=model.selected_count,
            error_type=model.error_type,
        )
