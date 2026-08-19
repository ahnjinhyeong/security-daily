from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from security_daily.infrastructure.database.base import Base


class AiAnalysisModel(Base):
    __tablename__ = "ai_analyses"
    __table_args__ = (
        CheckConstraint(
            "summary_status IN ('PENDING','RUNNING','SUCCESS','FAILED')",
            name="ck_ai_analyses_summary_status",
        ),
        CheckConstraint(
            "analyst_status IN ('PENDING','RUNNING','SUCCESS','FAILED')",
            name="ck_ai_analyses_analyst_status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str | None] = mapped_column(Text)
    importance: Mapped[str | None] = mapped_column(Text)
    attack_scenario: Mapped[str | None] = mapped_column(Text)
    security_actions: Mapped[list[str] | None] = mapped_column(JSONB)
    key_concepts: Mapped[list[dict[str, str]] | None] = mapped_column(JSONB)
    related_security_info: Mapped[list[dict[str, str]] | None] = mapped_column(JSONB)
    summary_model: Mapped[str | None] = mapped_column(Text)
    analyst_model: Mapped[str | None] = mapped_column(Text)
    summary_status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    analyst_status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    error_type: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
