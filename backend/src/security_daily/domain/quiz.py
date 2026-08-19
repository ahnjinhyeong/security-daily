from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Quiz:
    article_id: int
    quiz_date: date
    question: str
    answer: str
    accepted_answers: list[str]
    explanation: str
    model_name: str
    id: int | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class QuizAttempt:
    quiz_id: int
    user_answer: str
    is_correct: bool
    id: int | None = None
    answered_at: datetime | None = None
