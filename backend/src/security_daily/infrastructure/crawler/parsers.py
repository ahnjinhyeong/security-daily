import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from security_daily.infrastructure.crawler.dto import ArticleListItem, CrawledArticle
from security_daily.infrastructure.crawler.errors import CrawlerParseError


KST = ZoneInfo("Asia/Seoul")
LIST_DATE_PATTERN = re.compile(r"(\d{4}년\s+\d{2}월\s+\d{2}일\s+\d{2}:\d{2})")
DETAIL_DATE_PATTERN = re.compile(r"입력\s*:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})")


class BoanNewsListParser:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def parse(self, html: str) -> list[ArticleListItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[ArticleListItem] = []

        for container in soup.select("div.news_list"):
            link = container.select_one('a[href*="/media/view.asp?idx="]')
            title_node = container.select_one(".news_txt")
            writer_node = container.select_one(".news_writer")
            if link is None or title_node is None or writer_node is None:
                raise CrawlerParseError("Required article list markup is missing")

            href = link.get("href")
            if not isinstance(href, str):
                raise CrawlerParseError("Article link href is missing")
            source_article_ids = parse_qs(urlparse(href).query).get("idx")
            if not source_article_ids or not source_article_ids[0].isdigit():
                raise CrawlerParseError("Article idx is missing or invalid")

            date_match = LIST_DATE_PATTERN.search(writer_node.get_text(" ", strip=True))
            if date_match is None:
                raise CrawlerParseError("Article list published_at is missing")

            source_article_id = source_article_ids[0]
            items.append(
                ArticleListItem(
                    source_article_id=source_article_id,
                    url=f"{self._base_url}/media/view.asp?idx={source_article_id}",
                    title=title_node.get_text(" ", strip=True),
                    published_at=datetime.strptime(
                        date_match.group(1), "%Y년 %m월 %d일 %H:%M"
                    ).replace(tzinfo=KST),
                )
            )

        return items


class BoanNewsDetailParser:
    def parse(self, html: str, source_article_id: str, url: str) -> CrawledArticle:
        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.select_one("#news_title02 > h1")
        date_node = soup.select_one("#news_util01")
        body_node = soup.select_one('[itemprop="articleBody"] #news_content')
        if title_node is None or date_node is None or body_node is None:
            raise CrawlerParseError("Required article detail markup is missing")

        date_match = DETAIL_DATE_PATTERN.search(date_node.get_text(" ", strip=True))
        if date_match is None:
            raise CrawlerParseError("Article detail published_at is missing")

        content = self._clean_content(str(body_node))
        if not content:
            raise CrawlerParseError("Cleaned article content is empty")

        return CrawledArticle(
            source_article_id=source_article_id,
            url=url,
            title=title_node.get_text(" ", strip=True),
            content=content,
            published_at=datetime.strptime(
                date_match.group(1), "%Y-%m-%d %H:%M"
            ).replace(tzinfo=KST),
        )

    @staticmethod
    def _clean_content(body_html: str) -> str:
        body = BeautifulSoup(body_html, "html.parser")
        for node in body.select("figure, img, script, style, iframe"):
            node.decompose()
        for line_break in body.find_all("br"):
            line_break.replace_with("\n")

        text = body.get_text("\n", strip=True)
        text = re.sub(
            r"(?m)^\[보안뉴스\s+[^\]]+\s+기자\]\s*",
            "",
            text,
        )
        lines = []
        for raw_line in text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()
            if not line:
                continue
            if re.fullmatch(r"\[[^\]]+\s+기자(?:\([^)]*\))?\]", line):
                continue
            if "저작권자:" in line or "무단전재-재배포금지" in line:
                continue
            lines.append(line)
        return "\n\n".join(lines)
