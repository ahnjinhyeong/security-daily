from datetime import date
from typing import Protocol

from security_daily.domain.daily_selection import DailySelection


class DailySelectionRepository(Protocol):
    def replace_for_date(
        self, selection_date: date, selections: list[DailySelection]
    ) -> list[DailySelection]: ...

    def list_for_date(self, selection_date: date) -> list[DailySelection]: ...
