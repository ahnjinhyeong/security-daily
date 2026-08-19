from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from security_daily.agents.summary import SummaryAgent
from security_daily.domain import Article
from security_daily.infrastructure.llm.errors import LLMResponseError


class StubProvider:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
    def generate_json(self, **kwargs: Any) -> dict[str, Any]:
        return self.payload


def article() -> Article:
    now = datetime(2026, 8, 20, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    return Article("test", "1", "CVE 보안 기사", "https://example.test/1", "CVE-2026-0001 취약점이 제품에서 확인됐다.", now, now, id=1)


def test_summary_agent_accepts_fact_based_five_sentences() -> None:
    output = SummaryAgent(StubProvider({"summary": "첫째다. 둘째다. 셋째다. 넷째다. 다섯째다."}), "gemma3:4b", 12000).summarize(article())
    assert "다섯째" in output.summary


@pytest.mark.parametrize("summary", ["", "1. 2. 3. 4. 5. 6."])
def test_summary_agent_rejects_empty_or_more_than_five_sentences(summary: str) -> None:
    with pytest.raises(LLMResponseError):
        SummaryAgent(StubProvider({"summary": summary}), "gemma3:4b", 12000).summarize(article())
