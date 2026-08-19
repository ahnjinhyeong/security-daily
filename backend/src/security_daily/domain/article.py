from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Article:
    source: str
    source_article_id: str
    title: str
    url: str
    content: str
    published_at: datetime
    collected_at: datetime
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("source", "source_article_id", "title", "url", "content"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")

        if self.published_at.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        if self.collected_at.tzinfo is None:
            raise ValueError("collected_at must be timezone-aware")

