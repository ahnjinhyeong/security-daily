from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DailySelection:
    article_id: int
    selection_date: date
    rank: int
    score: Decimal
    reason: str
    model_name: str
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.article_id <= 0:
            raise ValueError("article_id must be positive")
        if not 1 <= self.rank <= 3:
            raise ValueError("rank must be between 1 and 3")
        if not Decimal("0") <= self.score <= Decimal("100"):
            raise ValueError("score must be between 0 and 100")
        if not self.reason.strip():
            raise ValueError("reason must not be blank")
        if not self.model_name.strip():
            raise ValueError("model_name must not be blank")
