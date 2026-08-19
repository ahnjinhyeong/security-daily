from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from security_daily.application import GetNewsBriefing
from security_daily.domain import BriefingArticle, NewsDateCount


class FakeNewsQueryRepository:
    def __init__(self, articles: list[BriefingArticle]) -> None:
        self.articles = articles
        self.requested_date: date | None = None

    def list_for_date(self, selection_date: date) -> list[BriefingArticle]:
        self.requested_date = selection_date
        return sorted(self.articles, key=lambda article: article.rank)

    def list_available_dates(self) -> list[NewsDateCount]:
        return [
            NewsDateCount(date(2026, 8, 19), 3),
            NewsDateCount(date(2026, 8, 18), 2),
        ]


def article(rank: int, article_id: int, summary: str | None = "요약") -> BriefingArticle:
    return BriefingArticle(
        rank=rank,
        article_id=article_id,
        title=f"선정 기사 {article_id}",
        url=f"https://example.test/{article_id}",
        published_at=datetime(2026, 8, 19, tzinfo=timezone.utc),
        summary=summary,
        importance="중요" if summary else None,
        attack_scenario="시나리오" if summary else None,
        security_actions=["조치"] if summary else None,
        key_concepts=[{"name": "RCE", "description": "설명"}] if summary else None,
        related_security_info=[] if summary else None,
    )


def test_today_uses_previous_day_in_kst_and_sorts_by_rank() -> None:
    repository = FakeNewsQueryRepository([article(2, 20), article(1, 10)])
    use_case = GetNewsBriefing(
        repository,
        clock=lambda: datetime(2026, 8, 20, 0, 30, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    result = use_case.for_today()

    assert result.date == date(2026, 8, 19)
    assert repository.requested_date == date(2026, 8, 19)
    assert [item.article_id for item in result.articles] == [10, 20]
    assert result.articles[0].summary == "요약"


def test_empty_date_returns_empty_briefing() -> None:
    result = GetNewsBriefing(FakeNewsQueryRepository([])).for_date(date(2099, 1, 1))
    assert result.count == 0
    assert result.articles == []


def test_available_dates_preserve_latest_first_counts() -> None:
    dates = GetNewsBriefing(FakeNewsQueryRepository([])).available_dates()
    assert [(item.date, item.article_count) for item in dates] == [
        (date(2026, 8, 19), 3),
        (date(2026, 8, 18), 2),
    ]
