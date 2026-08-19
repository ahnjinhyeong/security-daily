from datetime import date
from typing import Protocol

from security_daily.domain.quiz import Quiz


class QuizRepository(Protocol):
    def get_by_id(self, quiz_id: int) -> Quiz | None: ...
    def list_for_date(self, quiz_date: date) -> list[Quiz]: ...
    def save_for_date(self, quiz_date: date, quizzes: list[Quiz]) -> list[Quiz]: ...
