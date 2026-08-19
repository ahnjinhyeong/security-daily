from datetime import datetime
from zoneinfo import ZoneInfo

from security_daily.application import CollectDailyNews
from security_daily.domain import Article
from security_daily.infrastructure.crawler.dto import CrawledArticle


KST = ZoneInfo("Asia/Seoul")


class FakeCrawler:
    def collect(self, target_date: object) -> list[CrawledArticle]:
        return [
            CrawledArticle(
                source_article_id="100",
                url="https://www.boannews.com/media/view.asp?idx=100",
                title="수집 기사",
                content="정제 본문",
                published_at=datetime(2026, 8, 18, 12, 0, tzinfo=KST),
            ),
            CrawledArticle(
                source_article_id="101",
                url="https://www.boannews.com/media/view.asp?idx=101",
                title="중복 기사",
                content="정제 본문",
                published_at=datetime(2026, 8, 18, 13, 0, tzinfo=KST),
            ),
        ]


class FakeRepository:
    def __init__(self) -> None:
        self.saved: list[Article] = []

    def exists_by_source_id(self, source: str, source_article_id: str) -> bool:
        return source_article_id == "101"

    def add(self, article: Article) -> Article:
        self.saved.append(article)
        return article


def test_collect_daily_news_saves_new_articles_and_skips_duplicates() -> None:
    repository = FakeRepository()
    run_at = datetime(2026, 8, 19, 8, 30, tzinfo=KST)

    result = CollectDailyNews(
        FakeCrawler(), repository  # type: ignore[arg-type]
    ).execute(run_at)

    assert result.target_date.isoformat() == "2026-08-18"
    assert result.crawled_count == 2
    assert result.saved_count == 1
    assert result.duplicate_count == 1
    assert repository.saved[0].source == "boannews"
    assert repository.saved[0].collected_at == run_at

