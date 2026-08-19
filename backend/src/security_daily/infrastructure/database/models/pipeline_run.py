from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from security_daily.infrastructure.database.base import Base


class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')",
            name="ck_pipeline_runs_status",
        ),
        CheckConstraint(
            "stage IN ('COLLECT', 'SELECT', 'SUMMARY', 'ANALYZE', 'QUIZ')",
            name="ck_pipeline_runs_stage",
        ),
        CheckConstraint(
            "crawled_count >= 0 AND saved_count >= 0 AND duplicate_count >= 0",
            name="ck_pipeline_runs_counts_nonnegative",
        ),
        CheckConstraint(
            "candidate_count >= 0 AND selected_count >= 0",
            name="ck_pipeline_runs_selection_counts_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    crawled_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    saved_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    duplicate_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    candidate_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    selected_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_type: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
