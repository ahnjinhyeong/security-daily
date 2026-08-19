import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pytest

from security_daily.agents.selector import NewsSelectorAgent, SelectorInputBuilder
from security_daily.config import get_settings
from security_daily.domain import Article
from security_daily.infrastructure.llm import OllamaLLMProvider


KST = ZoneInfo("Asia/Seoul")


@pytest.mark.smoke
def test_live_ollama_selector_structured_output() -> None:
    if os.getenv("RUN_OLLAMA_SMOKE") != "1":
        pytest.skip("Set RUN_OLLAMA_SMOKE=1 to call the local Ollama API")

    settings = get_settings()
    try:
        tags = httpx.get(
            f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5
        )
        tags.raise_for_status()
    except httpx.HTTPError as error:
        pytest.fail(f"Ollama API is not reachable: {type(error).__name__}")

    installed = {model["name"].split(":", 1)[0] for model in tags.json()["models"]}
    requested = settings.selector_model.split(":", 1)[0]
    if requested not in installed:
        pytest.skip(f"Selector model is not installed: {settings.selector_model}")

    articles = [
        Article(
            id=1,
            source="smoke",
            source_article_id="1",
            title="원격 코드 실행 취약점 실제 악용 확인",
            url="https://example.test/1",
            content=(
                "인터넷에 노출된 서버에서 원격 코드 실행 취약점의 실제 악용이 "
                "확인됐다. 관리자는 패치를 적용하고 침해 지표를 점검해야 한다."
            ),
            published_at=datetime(2026, 8, 19, 10, 0, tzinfo=KST),
            collected_at=datetime(2026, 8, 20, 8, 30, tzinfo=KST),
        ),
        Article(
            id=2,
            source="smoke",
            source_article_id="2",
            title="보안 기업 행사 개최",
            url="https://example.test/2",
            content="보안 기업이 신제품 발표 행사를 개최했다.",
            published_at=datetime(2026, 8, 19, 11, 0, tzinfo=KST),
            collected_at=datetime(2026, 8, 20, 8, 30, tzinfo=KST),
        ),
    ]

    with OllamaLLMProvider(
        settings.ollama_base_url, settings.ollama_timeout_seconds
    ) as provider:
        decisions = NewsSelectorAgent(
            provider,
            settings.selector_model,
            SelectorInputBuilder(),
        ).select(articles)

    assert len(decisions) <= 3
    assert all(decision.article_id in {1, 2} for decision in decisions)
