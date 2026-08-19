from datetime import date
from typing import Protocol

from security_daily.domain.article import Article


class ArticleRepository(Protocol):
    def exists_by_source_id(self, source: str, source_article_id: str) -> bool: ...

    def add(self, article: Article) -> Article: ...

    def list_published_on(self, target_date: date) -> list[Article]: ...

    def get_by_ids(self, article_ids: list[int]) -> list[Article]: ...
