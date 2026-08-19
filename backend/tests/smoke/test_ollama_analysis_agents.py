import os
import re
from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

import pytest

from security_daily.agents.analyst import SecurityAnalystAgent
from security_daily.agents.summary import SummaryAgent
from security_daily.config import get_settings
from security_daily.domain import Article
from security_daily.infrastructure.llm import OllamaLLMProvider


@pytest.mark.smoke
def test_live_summary_and_analyst_agents() -> None:
    if os.getenv("RUN_OLLAMA_ANALYSIS_SMOKE") != "1":
        pytest.skip("Set RUN_OLLAMA_ANALYSIS_SMOKE=1 to call analysis models")
    settings = get_settings()
    now = datetime(2026, 8, 20, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    article = Article(
        "smoke",
        "analysis-1",
        "공공기관 대상 피싱 메일 증가",
        "https://example.test/analysis-1",
        "공공기관 직원을 대상으로 계정 확인을 유도하는 피싱 메일이 증가했다. 메일의 링크는 가짜 로그인 화면으로 연결되며 입력한 계정 정보를 탈취한다. 기사에는 특정 제품명이나 CVE가 공개되지 않았다.",
        now,
        now,
        id=1,
    )
    with OllamaLLMProvider(settings.ollama_base_url, settings.ollama_timeout_seconds) as provider:
        summary_started = perf_counter()
        summary = SummaryAgent(provider, settings.summary_model, 12000).summarize(article)
        summary_elapsed = perf_counter() - summary_started
        analyst_started = perf_counter()
        analysis = SecurityAnalystAgent(provider, settings.analyst_model, 12000).analyze(article, summary.summary)
        analyst_elapsed = perf_counter() - analyst_started

    assert summary.summary
    assert len(re.split(r"(?<=[.!?。])\s+", summary.summary)) <= 5
    assert re.search("[가-힣]", summary.summary)
    assert analysis.importance and analysis.attack_scenario
    assert len(analysis.security_actions) <= 5
    assert len(analysis.key_concepts) <= 5
    assert len(analysis.related_security_info) <= 5
    assert not any(item.type in {"CVE", "PRODUCT"} for item in analysis.related_security_info)
    assert summary_elapsed < settings.ollama_timeout_seconds
    assert analyst_elapsed < settings.ollama_timeout_seconds
