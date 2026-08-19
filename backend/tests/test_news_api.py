from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from security_daily.api.dependencies import get_news_query
from security_daily.api.main import app
from security_daily.application import NewsBriefing
from security_daily.domain import BriefingArticle, NewsDateCount


class FakeNewsQuery:
    def _briefing(self, target_date: date) -> NewsBriefing:
        if target_date == date(2099, 1, 1):
            return NewsBriefing(target_date, [])
        return NewsBriefing(
            target_date,
            [
                BriefingArticle(
                    rank=1,
                    article_id=11,
                    title="선정 기사",
                    url="https://example.test/11",
                    published_at=datetime(2026, 8, 19, tzinfo=timezone.utc),
                    summary="요약",
                    importance="중요",
                    attack_scenario="공격",
                    security_actions=["패치"],
                    key_concepts=[{"name": "RCE", "description": "원격 코드 실행"}],
                    related_security_info=[],
                )
            ],
        )

    def for_today(self) -> NewsBriefing:
        return self._briefing(date(2026, 8, 19))

    def for_date(self, target_date: date) -> NewsBriefing:
        return self._briefing(target_date)

    def available_dates(self) -> list[NewsDateCount]:
        return [NewsDateCount(date(2026, 8, 19), 1)]


def setup_module() -> None:
    app.dependency_overrides[get_news_query] = lambda: FakeNewsQuery()


def teardown_module() -> None:
    app.dependency_overrides.clear()


def test_today_news_response_schema_contains_selected_article_and_analysis() -> None:
    response = TestClient(app).get("/api/news/today")
    assert response.status_code == 200
    body = response.json()
    assert body["date"] == "2026-08-19"
    assert body["count"] == 1
    assert set(body["articles"][0]) == {
        "id", "rank", "title", "url", "published_at", "summary", "insight"
    }
    assert body["articles"][0]["insight"]["importance"] == "중요"


def test_news_by_date_empty_and_invalid_date() -> None:
    client = TestClient(app)
    empty = client.get("/api/news", params={"date": "2099-01-01"})
    assert empty.status_code == 200
    assert empty.json() == {"date": "2099-01-01", "count": 0, "articles": []}
    assert client.get("/api/news", params={"date": "not-a-date"}).status_code == 422


def test_news_dates() -> None:
    response = TestClient(app).get("/api/news/dates")
    assert response.status_code == 200
    assert response.json() == [{"date": "2026-08-19", "article_count": 1}]
