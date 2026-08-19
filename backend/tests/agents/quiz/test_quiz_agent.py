from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from security_daily.agents.quiz import QuizAgent
from security_daily.domain import AiAnalysis, AnalysisStatus, Article
from security_daily.infrastructure.llm.errors import LLMResponseError


class StubProvider:
    def __init__(self, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
        self.payloads = payload if isinstance(payload, list) else [payload]
        self.kwargs: dict[str, Any] = {}
        self.call_count = 0
    def generate_json(self, **kwargs: Any) -> dict[str, Any]:
        self.kwargs = kwargs
        payload = self.payloads[min(self.call_count, len(self.payloads) - 1)]
        self.call_count += 1
        return payload


def inputs(count: int = 1) -> list[tuple[Article, AiAnalysis]]:
    now = datetime(2026, 8, 20, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    return [
        (
            Article("test", str(index), f"기사 {index}", f"https://example.test/{index}", "원문", now, now, id=10 + index),
            AiAnalysis(10 + index, AnalysisStatus.SUCCESS, AnalysisStatus.SUCCESS, summary="요약", importance="중요", attack_scenario="공격", security_actions=["패치"], key_concepts=[{"name": f"개념 {index}", "description": "설명"}], related_security_info=[]),
        )
        for index in range(count)
    ]


def item(question: str = "원격 코드 실행의 약어는?", answer: str = "RCE", article_id: int = 10) -> dict[str, Any]:
    return {
        "article_id": article_id,
        "question": question,
        "answer": answer,
        "accepted_answers": [answer, answer.lower(), "Remote Code Execution"],
        "explanation": "원격 코드 실행을 의미한다.",
    }


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_quiz_agent_allows_zero_to_three_questions(count: int) -> None:
    candidate_count = max(1, count)
    payloads = [
        {"quizzes": [item(f"질문 {index}?", f"답 {index}", 10 + index)]}
        for index in range(count)
    ] or [{"quizzes": []}]
    result = QuizAgent(StubProvider(payloads), "llama3.2:3b").generate(inputs(candidate_count))
    assert len(result) == count


@pytest.mark.parametrize(
    "quizzes",
    [
        [item("같은 질문?", "A"), item("같은 질문?", "B")],
        [item(article_id=999)],
        [item(str(i), str(i)) for i in range(4)],
    ],
)
def test_quiz_agent_rejects_duplicates_unknown_ids_and_more_than_three(
    quizzes: list[dict[str, Any]],
) -> None:
    with pytest.raises(LLMResponseError):
        QuizAgent(StubProvider({"quizzes": quizzes}), "llama3.2:3b").generate(inputs())


def test_quiz_agent_rejects_duplicate_concepts_across_articles() -> None:
    provider = StubProvider([
        {"quizzes": [item("질문 A?", "RCE", 10)]},
        {"quizzes": [item("질문 B?", "rce", 11)]},
    ])
    with pytest.raises(LLMResponseError):
        QuizAgent(provider, "llama3.2:3b").generate(inputs(2))


def test_quiz_agent_deduplicates_accepted_answers() -> None:
    result = QuizAgent(StubProvider({"quizzes": [item()]}), "llama3.2:3b").generate(inputs())
    assert result[0].accepted_answers == ["Remote Code Execution"]


def test_quiz_agent_limits_ollama_output_without_including_article_content() -> None:
    provider = StubProvider({"quizzes": []})
    QuizAgent(provider, "llama3.2:3b").generate(inputs())

    assert provider.kwargs["max_output_tokens"] == 1024
    assert "원문" not in provider.kwargs["user_prompt"]
    quiz_schema = provider.kwargs["schema"]["$defs"]["QuizTransportItem"]["properties"]
    assert quiz_schema["question"]["maxLength"] == 100
    assert quiz_schema["explanation"]["maxLength"] == 200
