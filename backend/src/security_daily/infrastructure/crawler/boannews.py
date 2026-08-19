from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from security_daily.infrastructure.crawler.config import CrawlerConfig
from security_daily.infrastructure.crawler.dto import CrawledArticle
from security_daily.infrastructure.crawler.errors import (
    CrawlerPageLimitError,
    CrawlerParseError,
)
from security_daily.infrastructure.crawler.http_client import BoanNewsHttpClient
from security_daily.infrastructure.crawler.parsers import (
    BoanNewsDetailParser,
    BoanNewsListParser,
)


KST = ZoneInfo("Asia/Seoul")


def date_range_kst(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, time.min, tzinfo=KST)
    return start, start + timedelta(days=1)


def previous_date_kst(run_at: datetime) -> date:
    if run_at.tzinfo is None:
        raise ValueError("run_at must be timezone-aware")
    return run_at.astimezone(KST).date() - timedelta(days=1)


class BoanNewsCrawler:
    def __init__(
        self,
        config: CrawlerConfig,
        http_client: BoanNewsHttpClient,
        list_parser: BoanNewsListParser | None = None,
        detail_parser: BoanNewsDetailParser | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client
        self._list_parser = list_parser or BoanNewsListParser(config.base_url)
        self._detail_parser = detail_parser or BoanNewsDetailParser()

    def collect(self, target_date: date) -> list[CrawledArticle]:
        start, end = date_range_kst(target_date)
        seen_ids: set[str] = set()
        articles: list[CrawledArticle] = []

        for page in range(1, self._config.max_pages + 1):
            list_url = f"{self._config.base_url}/media/t_list.asp?Page={page}&kind="
            items = self._list_parser.parse(self._http_client.get_html(list_url))
            if not items:
                if page == 1:
                    raise CrawlerParseError("No articles found on the first list page")
                return articles

            for item in items:
                if item.source_article_id in seen_ids:
                    continue
                seen_ids.add(item.source_article_id)
                if not start <= item.published_at < end:
                    continue

                detail = self._detail_parser.parse(
                    self._http_client.get_html(item.url),
                    source_article_id=item.source_article_id,
                    url=item.url,
                )
                if start <= detail.published_at < end:
                    articles.append(detail)

            # 첫 페이지도 여러 기사 흐름이 섞일 수 있으므로 페이지 전체의 시각을 검사한다.
            if all(item.published_at < start for item in items):
                return articles

        raise CrawlerPageLimitError(
            f"Could not reach articles older than {target_date} within "
            f"{self._config.max_pages} pages"
        )
