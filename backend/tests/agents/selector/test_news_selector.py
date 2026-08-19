import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from security_daily.agents.selector import NewsSelectorAgent, SelectorInputBuilder
from security_daily.domain import Article
from security_daily.infrastructure.llm.errors import LLMResponseError


KST = ZoneInfo("Asia/Seoul")


class StubProvider:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    def generate_json(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return self.payload


def article(article_id: int, content: str = "보안 기사 본문") -> Article:
    return Article(
        id=article_id,
        source="boannews",
        source_article_id=str(article_id),
        title=f"보안 기사 {article_id}",
        url=f"https://www.boannews.com/media/view.asp?idx={article_id}",
        content=content,
        published_at=datetime(2026, 8, 18, 12, 0, tzinfo=KST),
        collected_at=datetime(2026, 8, 19, 8, 30, tzinfo=KST),
    )


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_selector_accepts_zero_to_three_ranked_selections(count: int) -> None:
    candidates = [article(index) for index in range(1, 4)]
    payload = {
        "selections": [
            {
                "article_id": index,
                "rank": index,
                "score": 90 - index,
                "reason": "실무 보안 학습 가치가 높음",
            }
            for index in range(1, count + 1)
        ]
    }
    provider = StubProvider(payload)
    selector = NewsSelectorAgent(
        provider, "phi4-mini", SelectorInputBuilder()
    )

    assert len(selector.select(candidates)) == count
    assert provider.calls[0]["model"] == "phi4-mini"
    assert "properties" in provider.calls[0]["schema"]
    assert provider.calls[0]["schema"]["$defs"]["SelectorDecision"][
        "properties"
    ]["article_id"]["enum"] == [1, 2, 3]


@pytest.mark.parametrize(
    "selections",
    [
        [
            {"article_id": 1, "rank": 1, "score": 90, "reason": "이유"},
            {"article_id": 1, "rank": 2, "score": 80, "reason": "이유"},
        ],
        [
            {"article_id": 1, "rank": 1, "score": 90, "reason": "이유"},
            {"article_id": 2, "rank": 1, "score": 80, "reason": "이유"},
        ],
        [{"article_id": 1, "rank": 4, "score": 90, "reason": "이유"}],
        [{"article_id": 999, "rank": 1, "score": 90, "reason": "이유"}],
        [{"article_id": 1, "rank": 1, "score": 101, "reason": "이유"}],
        [{"article_id": 1, "rank": 1, "score": 90, "reason": ""}],
        [
            {"article_id": 1, "rank": 1, "score": 90, "reason": "이유"},
            {"article_id": 2, "rank": 2, "score": 80, "reason": "이유"},
            {"article_id": 3, "rank": 3, "score": 70, "reason": "이유"},
            {"article_id": 4, "rank": 3, "score": 60, "reason": "이유"},
        ],
    ],
)
def test_selector_rejects_invalid_structured_output(
    selections: list[dict[str, object]],
) -> None:
    selector = NewsSelectorAgent(
        StubProvider({"selections": selections}),
        "phi4-mini",
        SelectorInputBuilder(),
    )

    with pytest.raises(LLMResponseError):
        selector.select([article(1), article(2)])


def test_input_builder_keeps_all_candidates_and_limits_content() -> None:
    builder = SelectorInputBuilder(max_content_chars=40, max_total_content_chars=80)

    payload = json.loads(
        builder.build([article(1, "가" * 100), article(2, "나" * 100)])
    )

    assert [item["article_id"] for item in payload["articles"]] == [1, 2]
    assert all("본문 일부 생략" in item["content_excerpt"] for item in payload["articles"])
    assert all(len(item["content_excerpt"]) <= 40 for item in payload["articles"])
    assert all(item["title"] for item in payload["articles"])
    assert all(item["published_at"] for item in payload["articles"])
