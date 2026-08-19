from datetime import date
from typing import Protocol

from security_daily.domain.news_briefing import BriefingArticle, NewsDateCount


class NewsQueryRepository(Protocol):
    def list_for_date(self, selection_date: date) -> list[BriefingArticle]: ...

    def list_available_dates(self) -> list[NewsDateCount]: ...
