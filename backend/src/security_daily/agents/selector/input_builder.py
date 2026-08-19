import json

from security_daily.domain import Article


class SelectorInputBuilder:
    def __init__(
        self,
        max_content_chars: int = 3000,
        max_total_content_chars: int = 24000,
    ) -> None:
        if max_content_chars < 1 or max_total_content_chars < 1:
            raise ValueError("selector content limits must be positive")
        self._max_content_chars = max_content_chars
        self._max_total_content_chars = max_total_content_chars

    def build(self, articles: list[Article]) -> str:
        if not articles:
            return json.dumps({"articles": []}, ensure_ascii=False)

        # 모든 후보를 유지하면서 기사 수에 따라 본문 예산을 공평하게 배분한다.
        per_article_limit = min(
            self._max_content_chars,
            max(1, self._max_total_content_chars // len(articles)),
        )
        candidates = []
        for article in articles:
            if article.id is None:
                raise ValueError("selector candidates must have persisted article ids")
            candidates.append(
                {
                    "article_id": article.id,
                    "title": article.title,
                    "published_at": article.published_at.isoformat(),
                    "content_excerpt": self._excerpt(
                        article.content, per_article_limit
                    ),
                }
            )
        return json.dumps({"articles": candidates}, ensure_ascii=False)

    @staticmethod
    def _excerpt(content: str, limit: int) -> str:
        if len(content) <= limit:
            return content
        marker = "\n...[본문 일부 생략]...\n"
        if limit <= len(marker) + 2:
            return content[:limit]
        # 결론이나 영향 정보가 후반에 있는 경우를 위해 앞부분과 끝부분을 함께 보존한다.
        content_budget = limit - len(marker)
        tail_length = max(1, content_budget // 4)
        head_length = content_budget - tail_length
        return f"{content[:head_length]}{marker}{content[-tail_length:]}"
