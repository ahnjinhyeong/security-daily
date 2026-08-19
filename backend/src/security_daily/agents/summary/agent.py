import json

from pydantic import ValidationError

from security_daily.agents.summary.schemas import SummaryOutput
from security_daily.domain import Article
from security_daily.infrastructure.llm.errors import LLMResponseError
from security_daily.infrastructure.llm.provider import LLMProvider


SYSTEM_PROMPT = """기사에서 확인되는 사실만 최대 5문장으로 한국어 요약하라.
핵심 사건, 대상, 원인, 영향을 우선하고 CVE·제품명·기관명·공격명은 유지한다.
추측, 보안 분석, 대응 조언, 기사에 없는 사실은 추가하지 않는다."""


class SummaryAgent:
    def __init__(self, provider: LLMProvider, model_name: str, max_content_chars: int) -> None:
        self._provider = provider
        self.model_name = model_name
        self._max_content_chars = max_content_chars

    def summarize(self, article: Article) -> SummaryOutput:
        if article.id is None:
            raise ValueError("summary article must have a persisted id")
        content = article.content[: self._max_content_chars]
        prompt = json.dumps(
            {
                "article_id": article.id,
                "title": article.title,
                "published_at": article.published_at.isoformat(),
                "content": content,
            },
            ensure_ascii=False,
        )
        payload = self._provider.generate_json(
            model=self.model_name,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            schema=SummaryOutput.model_json_schema(),
        )
        try:
            return SummaryOutput.model_validate(payload)
        except ValidationError as error:
            raise LLMResponseError("Summary output validation failed") from error
