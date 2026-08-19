from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from security_daily.infrastructure.crawler.boannews import (
    BoanNewsCrawler,
    date_range_kst,
    previous_date_kst,
)
from security_daily.infrastructure.crawler.config import CrawlerConfig
from security_daily.infrastructure.crawler.errors import CrawlerParseError


KST = ZoneInfo("Asia/Seoul")


def list_html(*items: tuple[str, str]) -> str:
    blocks = []
    for source_id, published_at in items:
        blocks.append(
            f"""
            <div class="news_list">
              <a href="/media/view.asp?idx={source_id}&amp;page=1&amp;kind=4">
                <span class="news_txt">기사 {source_id}</span>
              </a>
              <span class="news_writer">기자 | {published_at}</span>
            </div>
            """
        )
    return "<html><body>" + "".join(blocks) + "</body></html>"


def detail_html(source_id: str, published_at: str) -> str:
    return f"""
    <div id="news_title02"><h1>기사 {source_id}</h1></div>
    <div id="news_util01">입력 : {published_at}</div>
    <div itemprop="articleBody"><div id="news_content">본문 {source_id}</div></div>
    """


class FakeHttpClient:
    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = responses
        self.requested_urls: list[str] = []

    def get_html(self, url: str) -> str:
        self.requested_urls.append(url)
        return self.responses[url]


def make_config() -> CrawlerConfig:
    return CrawlerConfig(
        base_url="https://www.boannews.com",
        timeout_seconds=1,
        max_retries=0,
        max_pages=5,
        user_agent="SecurityDaily/Test",
    )


def test_date_range_and_previous_date_use_kst() -> None:
    start, end = date_range_kst(date(2026, 8, 18))

    assert start == datetime(2026, 8, 18, 0, 0, tzinfo=KST)
    assert end == datetime(2026, 8, 19, 0, 0, tzinfo=KST)
    assert previous_date_kst(datetime(2026, 8, 19, 8, 30, tzinfo=KST)) == date(
        2026, 8, 18
    )


def test_crawler_paginates_filters_and_deduplicates_idx() -> None:
    base = "https://www.boannews.com"
    responses = {
        f"{base}/media/t_list.asp?Page=1&kind=": list_html(
            ("200", "2026년 08월 19일 07:00"),
            ("100", "2026년 08월 18일 15:45"),
        ),
        f"{base}/media/t_list.asp?Page=2&kind=": list_html(
            ("100", "2026년 08월 18일 15:45"),
            ("099", "2026년 08월 17일 23:59"),
        ),
        f"{base}/media/t_list.asp?Page=3&kind=": list_html(
            ("098", "2026년 08월 17일 20:00"),
        ),
        f"{base}/media/view.asp?idx=100": detail_html("100", "2026-08-18 15:45"),
    }
    http_client = FakeHttpClient(responses)

    articles = BoanNewsCrawler(
        make_config(), http_client  # type: ignore[arg-type]
    ).collect(date(2026, 8, 18))

    assert [article.source_article_id for article in articles] == ["100"]
    assert http_client.requested_urls.count(f"{base}/media/view.asp?idx=100") == 1
    assert f"{base}/media/t_list.asp?Page=3&kind=" in http_client.requested_urls
    assert f"{base}/media/t_list.asp?Page=4&kind=" not in http_client.requested_urls


def test_crawler_reports_empty_first_page_as_site_change() -> None:
    base = "https://www.boannews.com"
    http_client = FakeHttpClient(
        {f"{base}/media/t_list.asp?Page=1&kind=": "<html></html>"}
    )

    with pytest.raises(CrawlerParseError, match="first list page"):
        BoanNewsCrawler(
            make_config(), http_client  # type: ignore[arg-type]
        ).collect(date(2026, 8, 18))
