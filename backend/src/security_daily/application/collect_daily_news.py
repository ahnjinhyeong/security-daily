from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from security_daily.domain import Article
from security_daily.domain.repositories import ArticleRepository
from security_daily.infrastructure.crawler.boannews import previous_date_kst
from security_daily.infrastructure.crawler.dto import CrawledArticle


class DailyArticleCrawler(Protocol):
    def collect(self, target_date: date) -> list[CrawledArticle]: ...


@dataclass(frozen=True, slots=True)
class CollectDailyNewsResult:
    target_date: date
    crawled_count: int
    saved_count: int
    duplicate_count: int


class CollectDailyNews:
    def __init__(
        self,
        crawler: DailyArticleCrawler,
        repository: ArticleRepository,
    ) -> None:
        self._crawler = crawler
        self._repository = repository

    def execute(self, run_at: datetime) -> CollectDailyNewsResult:
        target_date = previous_date_kst(run_at)
        crawled_articles = self._crawler.collect(target_date)
        saved_count = 0
        duplicate_count = 0

        for crawled in crawled_articles:
            if self._repository.exists_by_source_id(
                "boannews", crawled.source_article_id
            ):
                duplicate_count += 1
                continue
            self._repository.add(
                Article(
                    source="boannews",
                    source_article_id=crawled.source_article_id,
                    title=crawled.title,
                    url=crawled.url,
                    content=crawled.content,
                    published_at=crawled.published_at,
                    collected_at=run_at,
                )
            )
            saved_count += 1

        return CollectDailyNewsResult(
            target_date=target_date,
            crawled_count=len(crawled_articles),
            saved_count=saved_count,
            duplicate_count=duplicate_count,
        )

