from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from security_daily.infrastructure.crawler.errors import CrawlerParseError
from security_daily.infrastructure.crawler.parsers import (
    BoanNewsDetailParser,
    BoanNewsListParser,
)


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "boannews"
KST = ZoneInfo("Asia/Seoul")


def load_fixture(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text(encoding="utf-8")


def test_list_parser_extracts_canonical_article_data() -> None:
    parser = BoanNewsListParser("https://www.boannews.com")

    items = parser.parse(load_fixture("list_page.html"))

    assert len(items) == 1
    assert items[0].source_article_id == "145190"
    assert items[0].url == "https://www.boannews.com/media/view.asp?idx=145190"
    assert items[0].title == "테스트 보안 기사"
    assert items[0].published_at == datetime(2026, 8, 18, 15, 45, tzinfo=KST)


def test_list_parser_fails_when_required_markup_changes() -> None:
    parser = BoanNewsListParser("https://www.boannews.com")

    with pytest.raises(CrawlerParseError, match="list markup"):
        parser.parse('<div class="news_list"><span>changed</span></div>')


def test_detail_parser_extracts_and_cleans_text_content() -> None:
    parser = BoanNewsDetailParser()

    article = parser.parse(
        load_fixture("detail_page.html"),
        source_article_id="145190",
        url="https://www.boannews.com/media/view.asp?idx=145190",
    )

    assert article.title == "테스트 보안 기사"
    assert article.published_at == datetime(2026, 8, 18, 15, 45, tzinfo=KST)
    assert article.content == (
        "테스트 부제\n\n첫 번째 본문 문장입니다.\n\n두 번째 본문 문장입니다."
    )
    assert "test.jpg" not in article.content
    assert "저작권자" not in article.content


def test_detail_parser_fails_when_required_markup_changes() -> None:
    parser = BoanNewsDetailParser()

    with pytest.raises(CrawlerParseError, match="detail markup"):
        parser.parse("<html></html>", "145190", "https://example.test/article")

