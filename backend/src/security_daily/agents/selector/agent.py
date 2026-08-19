from pydantic import ValidationError

from security_daily.agents.selector.input_builder import SelectorInputBuilder
from security_daily.agents.selector.schemas import SelectorDecision, SelectorOutput
from security_daily.domain import Article
from security_daily.infrastructure.llm.errors import LLMResponseError
from security_daily.infrastructure.llm.provider import LLMProvider


SYSTEM_PROMPT = """당신은 보안 학습용 뉴스 선별 전문가다.
제공된 후보 기사만 평가하여 학습 가치가 충분한 기사를 최대 3개 선정한다.
실무 보안 중요도, 실제 공격·취약점 관련성, 영향 범위, 학습 가치, 기사 간 중복성,
홍보·행사·단순 업계 동향 여부를 종합 평가한다.
가치가 부족하면 3개를 채우지 말고 빈 목록 또는 1~2개만 반환한다.
article_id는 목록 순번을 만들지 말고 입력에 제공된 실제 값을 그대로 복사한다.
점수는 0~1 비율이 아닌 0~100 정수이며 높은 점수가 높은 학습 가치를 뜻한다.
rank는 1부터 연속되어야 하며 reason은 한국어로 간결하게 작성한다."""


class NewsSelectorAgent:
    def __init__(
        self,
        provider: LLMProvider,
        model_name: str,
        input_builder: SelectorInputBuilder,
    ) -> None:
        self._provider = provider
        self.model_name = model_name
        self._input_builder = input_builder

    def select(self, articles: list[Article]) -> list[SelectorDecision]:
        if not articles:
            return []

        schema = SelectorOutput.model_json_schema()
        # Ollama 단계에서도 후보 밖 ID를 생성하지 못하도록 실행별 Schema를 좁힌다.
        schema["$defs"]["SelectorDecision"]["properties"]["article_id"][
            "enum"
        ] = sorted(article.id for article in articles if article.id is not None)
        payload = self._provider.generate_json(
            model=self.model_name,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=self._input_builder.build(articles),
            schema=schema,
        )
        try:
            output = SelectorOutput.model_validate(payload)
        except ValidationError as error:
            raise LLMResponseError("Selector output schema validation failed") from error

        candidate_ids = {article.id for article in articles}
        unknown_ids = {
            decision.article_id
            for decision in output.selections
            if decision.article_id not in candidate_ids
        }
        if unknown_ids:
            raise LLMResponseError("Selector returned an unknown article_id")
        return sorted(output.selections, key=lambda item: item.rank)
