from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from security_daily.infrastructure.database.base import Base


class DailySelectionModel(Base):
    __tablename__ = "daily_selections"
    __table_args__ = (
        UniqueConstraint(
            "selection_date", "rank", name="uq_daily_selections_date_rank"
        ),
        UniqueConstraint(
            "selection_date",
            "article_id",
            name="uq_daily_selections_date_article",
        ),
        CheckConstraint("rank BETWEEN 1 AND 3", name="ck_daily_selections_rank"),
        CheckConstraint(
            "score BETWEEN 0 AND 100", name="ck_daily_selections_score"
        ),
        Index("ix_daily_selections_selection_date", "selection_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    selection_date: Mapped[date] = mapped_column(Date, nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

