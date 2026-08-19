import json

from pydantic import ValidationError

from security_daily.agents.analyst.schemas import AnalystOutput
from security_daily.domain import Article
from security_daily.infrastructure.llm.errors import LLMResponseError
from security_daily.infrastructure.llm.provider import LLMProvider


SYSTEM_PROMPT = """기사 원문을 최우선 근거로 보안적 의미를 한국어로 분석하라.
importance는 중요성을 2~3문장, attack_scenario는 2~4문장으로 작성한다.
실제 악용이 기사에 있으면 ACTUAL, 일반 지식 기반 가능성은 POSSIBLE이라고 명시한다.
보안 조치는 최대 5개, 핵심 개념과 관련 정보는 각각 최대 5개다.
기사에 없는 CVE·제품·실제 악용 사실을 만들지 말고 확인되지 않으면 빈 배열을 반환한다."""


class SecurityAnalystAgent:
    def __init__(self, provider: LLMProvider, model_name: str, max_content_chars: int) -> None:
        self._provider = provider
        self.model_name = model_name
        self._max_content_chars = max_content_chars

    def analyze(self, article: Article, summary: str) -> AnalystOutput:
        if article.id is None:
            raise ValueError("analysis article must have a persisted id")
        prompt = json.dumps(
            {
                "article_id": article.id,
                "title": article.title,
                "published_at": article.published_at.isoformat(),
                "content": article.content[: self._max_content_chars],
                "summary": summary,
            },
            ensure_ascii=False,
        )
        payload = self._provider.generate_json(
            model=self.model_name,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            schema=AnalystOutput.model_json_schema(),
        )
        try:
            return AnalystOutput.model_validate(payload)
        except ValidationError as error:
            raise LLMResponseError("Analyst output validation failed") from error
