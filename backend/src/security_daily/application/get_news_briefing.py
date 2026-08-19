from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from security_daily.domain import BriefingArticle, NewsDateCount
from security_daily.domain.repositories import NewsQueryRepository


@dataclass(frozen=True, slots=True)
class NewsBriefing:
    date: date
    articles: list[BriefingArticle]

    @property
    def count(self) -> int:
        return len(self.articles)


def _now() -> datetime:
    return datetime.now(tz=ZoneInfo("Asia/Seoul"))


class GetNewsBriefing:
    def __init__(
        self,
        repository: NewsQueryRepository,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def for_date(self, target_date: date) -> NewsBriefing:
        return NewsBriefing(target_date, self._repository.list_for_date(target_date))

    def for_today(self) -> NewsBriefing:
        # Morning Briefing은 Asia/Seoul 기준 전날 Pipeline 결과를 보여준다.
        target_date = self._clock().astimezone(ZoneInfo("Asia/Seoul")).date() - timedelta(days=1)
        return self.for_date(target_date)

    def available_dates(self) -> list[NewsDateCount]:
        return self._repository.list_available_dates()
