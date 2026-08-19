from typing import Protocol

from security_daily.domain.quiz import QuizAttempt


class QuizAttemptRepository(Protocol):
    def add(self, attempt: QuizAttempt) -> QuizAttempt: ...
