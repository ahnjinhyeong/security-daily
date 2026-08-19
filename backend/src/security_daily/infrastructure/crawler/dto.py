from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ArticleListItem:
    source_article_id: str
    url: str
    title: str
    published_at: datetime


@dataclass(frozen=True, slots=True)
class CrawledArticle:
    source_article_id: str
    url: str
    title: str
    content: str
    published_at: datetime

