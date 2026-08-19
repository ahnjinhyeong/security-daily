from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from security_daily.agents.selector.schemas import SelectorDecision
from security_daily.application import SelectDailyNews
from security_daily.domain import Article, DailySelection


KST = ZoneInfo("Asia/Seoul")
TARGET_DATE = date(2026, 8, 18)
SELECTED_AT = datetime(2026, 8, 19, 8, 30, tzinfo=KST)


class FakeArticleRepository:
    def __init__(self) -> None:
        self.articles = [
            Article(
                id=1,
                source="boannews",
                source_article_id="1",
                title="기사",
                url="https://www.boannews.com/media/view.asp?idx=1",
                content="정제 본문",
                published_at=datetime(2026, 8, 18, 12, 0, tzinfo=KST),
                collected_at=SELECTED_AT,
            )
        ]

    def list_published_on(self, target_date: date) -> list[Article]:
        return self.articles


class FakeSelectionRepository:
    def __init__(self) -> None:
        self.by_date: dict[date, list[DailySelection]] = {}

    def replace_for_date(
        self, selection_date: date, selections: list[DailySelection]
    ) -> list[DailySelection]:
        self.by_date[selection_date] = selections
        return selections


class StubSelector:
    model_name = "phi4-mini"

    def __init__(self, score: str = "90") -> None:
        self.score = score

    def select(self, articles: list[Article]) -> list[SelectorDecision]:
        return [
            SelectorDecision(
                article_id=1,
                rank=1,
                score=Decimal(self.score),
                reason=f"점수 {self.score} 선정",
            )
        ]


def test_select_daily_news_saves_validated_results() -> None:
    repository = FakeSelectionRepository()
    timer = iter((1.0, 2.0))
    use_case = SelectDailyNews(
        FakeArticleRepository(),  # type: ignore[arg-type]
        repository,
        StubSelector(),
        timer=lambda: next(timer),
    )

    result = use_case.execute(TARGET_DATE, SELECTED_AT)

    assert result.candidate_count == 1
    assert result.selected_count == 1
    assert result.elapsed_seconds == 1.0
    saved = repository.by_date[TARGET_DATE][0]
    assert saved.article_id == 1
    assert saved.model_name == "phi4-mini"


def test_select_daily_news_replaces_same_date_results() -> None:
    repository = FakeSelectionRepository()
    first_timer = iter((1.0, 2.0))
    second_timer = iter((3.0, 4.0))

    SelectDailyNews(
        FakeArticleRepository(),  # type: ignore[arg-type]
        repository,
        StubSelector("90"),
        timer=lambda: next(first_timer),
    ).execute(TARGET_DATE, SELECTED_AT)
    SelectDailyNews(
        FakeArticleRepository(),  # type: ignore[arg-type]
        repository,
        StubSelector("70"),
        timer=lambda: next(second_timer),
    ).execute(TARGET_DATE, SELECTED_AT)

    assert len(repository.by_date[TARGET_DATE]) == 1
    assert repository.by_date[TARGET_DATE][0].score == Decimal("70")

