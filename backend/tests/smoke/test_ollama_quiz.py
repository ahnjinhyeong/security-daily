import os
from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

import pytest

from security_daily.agents.quiz import QuizAgent
from security_daily.config import get_settings
from security_daily.domain import AiAnalysis, AnalysisStatus, Article
from security_daily.infrastructure.llm import OllamaLLMProvider


@pytest.mark.smoke
def test_live_ollama_quiz_agent() -> None:
    if os.getenv("RUN_OLLAMA_QUIZ_SMOKE") != "1":
        pytest.skip("Set RUN_OLLAMA_QUIZ_SMOKE=1 to call the quiz model")
    settings = get_settings()
    now = datetime(2026, 8, 20, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    article = Article("smoke", "quiz-1", "RCE 취약점", "https://example.test/quiz-1", "사용하지 않는 원문", now, now, id=1)
    analysis = AiAnalysis(
        1,
        AnalysisStatus.SUCCESS,
        AnalysisStatus.SUCCESS,
        summary="원격 코드 실행 취약점이 확인됐다.",
        importance="원격 공격 위험이 있어 중요하다.",
        attack_scenario="POSSIBLE: 공격자가 임의 코드를 실행할 수 있다.",
        security_actions=["패치를 적용한다."],
        key_concepts=[{"name": "RCE", "description": "원격 코드 실행"}],
        related_security_info=[{"type": "VULNERABILITY", "value": "RCE"}],
    )
    started = perf_counter()
    with OllamaLLMProvider(settings.ollama_base_url, settings.ollama_timeout_seconds) as provider:
        quizzes = QuizAgent(provider, settings.quiz_model).generate([(article, analysis)])
    elapsed = perf_counter() - started
    assert len(quizzes) <= 3
    assert all(quiz.article_id == 1 for quiz in quizzes)
    assert elapsed < settings.ollama_timeout_seconds
