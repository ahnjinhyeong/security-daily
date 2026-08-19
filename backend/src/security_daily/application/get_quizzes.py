from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from security_daily.domain.repositories import QuizRepository


@dataclass(frozen=True, slots=True)
class PublicQuiz:
    id: int
    article_id: int
    question: str


def _now() -> datetime:
    return datetime.now(tz=ZoneInfo("Asia/Seoul"))


class GetQuizzes:
    def __init__(
        self,
        repository: QuizRepository,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def for_date(self, quiz_date: date) -> list[PublicQuiz]:
        return [
            PublicQuiz(id=quiz.id, article_id=quiz.article_id, question=quiz.question)
            for quiz in self._repository.list_for_date(quiz_date)
            if quiz.id is not None
        ]

    def for_today_briefing(self) -> list[PublicQuiz]:
        # 08:30 KST Morning Briefing은 전날 처리 날짜의 결과를 노출한다.
        target_date = self._clock().astimezone(ZoneInfo("Asia/Seoul")).date() - timedelta(days=1)
        return self.for_date(target_date)
