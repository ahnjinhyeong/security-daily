import re
from dataclasses import dataclass

from security_daily.domain import QuizAttempt
from security_daily.domain.repositories import QuizAttemptRepository, QuizRepository


class QuizNotFoundError(Exception):
    """요청한 Quiz가 존재하지 않을 때 발생한다."""


class EmptyQuizAnswerError(ValueError):
    """공백뿐인 답안 제출을 거부한다."""


def normalize_quiz_answer(value: str) -> str:
    """의미를 바꾸지 않고 공백과 영문 대소문자 차이만 정규화한다."""
    return re.sub(r"\s+", " ", value.strip()).casefold()


def is_quiz_answer_correct(
    user_answer: str, correct_answer: str, accepted_answers: list[str]
) -> bool:
    normalized = normalize_quiz_answer(user_answer)
    if not normalized:
        raise EmptyQuizAnswerError("answer must not be blank")
    valid_answers = {normalize_quiz_answer(correct_answer)}
    valid_answers.update(normalize_quiz_answer(answer) for answer in accepted_answers)
    return normalized in valid_answers


@dataclass(frozen=True, slots=True)
class GradeQuizAnswerResult:
    correct: bool
    correct_answer: str
    explanation: str


class GradeQuizAnswer:
    def __init__(
        self,
        quiz_repository: QuizRepository,
        attempt_repository: QuizAttemptRepository,
    ) -> None:
        self._quiz_repository = quiz_repository
        self._attempt_repository = attempt_repository

    def execute(self, quiz_id: int, user_answer: str) -> GradeQuizAnswerResult:
        quiz = self._quiz_repository.get_by_id(quiz_id)
        if quiz is None:
            raise QuizNotFoundError(f"quiz {quiz_id} was not found")

        correct = is_quiz_answer_correct(
            user_answer, quiz.answer, quiz.accepted_answers
        )
        self._attempt_repository.add(
            QuizAttempt(
                quiz_id=quiz_id,
                # 원문 답안을 학습 기록으로 보존하되 공백뿐인 값은 위에서 차단한다.
                user_answer=user_answer,
                is_correct=correct,
            )
        )
        return GradeQuizAnswerResult(correct, quiz.answer, quiz.explanation)
