from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class BriefingArticle:
    rank: int
    article_id: int
    title: str
    url: str
    published_at: datetime
    summary: str | None
    importance: str | None
    attack_scenario: str | None
    security_actions: list[str] | None
    key_concepts: list[dict[str, str]] | None
    related_security_info: list[dict[str, str]] | None


@dataclass(frozen=True, slots=True)
class NewsDateCount:
    date: date
    article_count: int
