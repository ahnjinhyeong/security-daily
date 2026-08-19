from datetime import date

from fastapi.testclient import TestClient

from security_daily.api.dependencies import get_quiz_grader, get_quiz_query
from security_daily.api.main import app
from security_daily.application import GradeQuizAnswerResult, PublicQuiz, QuizNotFoundError


class FakeQuery:
    def for_today_briefing(self) -> list[PublicQuiz]:
        return [PublicQuiz(id=1, article_id=2, question="질문?")]

    def for_date(self, quiz_date: date) -> list[PublicQuiz]:
        assert quiz_date == date(2026, 8, 18)
        return [PublicQuiz(id=3, article_id=4, question="과거 질문?")]


class FakeGrader:
    def execute(self, quiz_id: int, user_answer: str) -> GradeQuizAnswerResult:
        if quiz_id == 999:
            raise QuizNotFoundError
        return GradeQuizAnswerResult(
            correct=user_answer.casefold() == "rce",
            correct_answer="RCE",
            explanation="해설",
        )


def setup_module() -> None:
    app.dependency_overrides[get_quiz_query] = lambda: FakeQuery()
    app.dependency_overrides[get_quiz_grader] = lambda: FakeGrader()


def teardown_module() -> None:
    app.dependency_overrides.clear()


def test_today_quizzes_do_not_expose_answers() -> None:
    response = TestClient(app).get("/api/quizzes/today")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "article_id": 2, "question": "질문?"}]
    assert set(response.json()[0]) == {"id", "article_id", "question"}


def test_quizzes_by_date() -> None:
    response = TestClient(app).get("/api/quizzes", params={"date": "2026-08-18"})
    assert response.status_code == 200
    assert response.json()[0]["id"] == 3


def test_submit_answer_and_validation_errors() -> None:
    client = TestClient(app)
    response = client.post("/api/quizzes/1/answer", json={"answer": "rce"})
    assert response.status_code == 200
    assert response.json() == {
        "correct": True,
        "correct_answer": "RCE",
        "explanation": "해설",
    }
    assert client.post("/api/quizzes/1/answer", json={"answer": "   "}).status_code == 422
    assert client.post("/api/quizzes/999/answer", json={"answer": "RCE"}).status_code == 404
