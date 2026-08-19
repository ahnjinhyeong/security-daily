from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from security_daily.application import (
    EmptyQuizAnswerError,
    GetQuizzes,
    GradeQuizAnswer,
    QuizNotFoundError,
    is_quiz_answer_correct,
    normalize_quiz_answer,
)
from security_daily.domain import Quiz, QuizAttempt


class FakeQuizRepository:
    def __init__(self, quizzes: list[Quiz]) -> None:
        self.quizzes = quizzes
        self.requested_dates: list[date] = []

    def get_by_id(self, quiz_id: int) -> Quiz | None:
        return next((quiz for quiz in self.quizzes if quiz.id == quiz_id), None)

    def list_for_date(self, quiz_date: date) -> list[Quiz]:
        self.requested_dates.append(quiz_date)
        return [quiz for quiz in self.quizzes if quiz.quiz_date == quiz_date]

    def save_for_date(self, quiz_date: date, quizzes: list[Quiz]) -> list[Quiz]:
        raise NotImplementedError


class FakeAttemptRepository:
    def __init__(self) -> None:
        self.attempts: list[QuizAttempt] = []

    def add(self, attempt: QuizAttempt) -> QuizAttempt:
        saved = QuizAttempt(
            id=len(self.attempts) + 1,
            quiz_id=attempt.quiz_id,
            user_answer=attempt.user_answer,
            is_correct=attempt.is_correct,
            answered_at=attempt.answered_at,
        )
        self.attempts.append(saved)
        return saved


def make_quiz() -> Quiz:
    return Quiz(
        id=10,
        article_id=20,
        quiz_date=date(2026, 8, 18),
        question="원격 코드 실행의 약어는?",
        answer="RCE",
        accepted_answers=["Remote Code Execution", "원격 코드 실행"],
        explanation="RCE는 원격 코드 실행입니다.",
        model_name="test",
    )


@pytest.mark.parametrize(
    "value",
    ["RCE", "rce", "  RCE  ", "Remote   Code Execution", "원격 코드 실행"],
)
def test_answer_variants_are_correct(value: str) -> None:
    quiz = make_quiz()
    assert is_quiz_answer_correct(value, quiz.answer, quiz.accepted_answers)


def test_wrong_and_blank_answers() -> None:
    quiz = make_quiz()
    assert not is_quiz_answer_correct("SQL Injection", quiz.answer, quiz.accepted_answers)
    with pytest.raises(EmptyQuizAnswerError):
        is_quiz_answer_correct(" \t ", quiz.answer, quiz.accepted_answers)


def test_normalize_only_changes_case_and_whitespace() -> None:
    assert normalize_quiz_answer("  Remote\t Code  Execution ") == "remote code execution"
    assert normalize_quiz_answer("RCE 공격") != normalize_quiz_answer("RCE")


def test_grade_stores_attempt_and_returns_answer_details() -> None:
    attempts = FakeAttemptRepository()
    result = GradeQuizAnswer(FakeQuizRepository([make_quiz()]), attempts).execute(10, "rce")

    assert result.correct is True
    assert result.correct_answer == "RCE"
    assert result.explanation
    assert attempts.attempts[0].user_answer == "rce"
    assert attempts.attempts[0].is_correct is True


def test_grade_rejects_unknown_quiz_without_attempt() -> None:
    attempts = FakeAttemptRepository()
    with pytest.raises(QuizNotFoundError):
        GradeQuizAnswer(FakeQuizRepository([]), attempts).execute(999, "RCE")
    assert attempts.attempts == []


def test_today_uses_previous_kst_date_and_public_fields_only() -> None:
    repository = FakeQuizRepository([make_quiz()])
    use_case = GetQuizzes(
        repository,
        clock=lambda: datetime(2026, 8, 19, 8, 30, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    result = use_case.for_today_briefing()

    assert repository.requested_dates == [date(2026, 8, 18)]
    assert result[0].id == 10
    assert not hasattr(result[0], "answer")
    assert not hasattr(result[0], "accepted_answers")
    assert not hasattr(result[0], "explanation")
