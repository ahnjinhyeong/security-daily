import json

from pydantic import ValidationError

from security_daily.agents.quiz.schemas import QuizItem, QuizOutput, QuizTransportOutput
from security_daily.domain import AiAnalysis, Article
from security_daily.infrastructure.llm.errors import LLMResponseError
from security_daily.infrastructure.llm.provider import LLMProvider


SYSTEM_PROMPT = """제공된 한 기사의 제목, 요약, 보안 분석만 근거로 한국어 단답형 퀴즈를 최대 1개 생성하라.
학습 가치가 높은 핵심 개념을 우선하고 가치가 부족하면 문제를 만들지 않는다.
같은 개념을 반복 출제하지 말고 정답은 명확하고 짧게 작성한다.
accepted_answers에는 정답과 의미가 같은 표현만 최대 3개 넣는다.
질문은 100자 이내의 1문장, 정답은 30자 이내, 해설은 200자 이내의 2문장으로 작성한다.
기사나 분석에 없는 사실을 만들지 않는다."""

QUIZ_MAX_OUTPUT_TOKENS = 1024


class QuizAgent:
    def __init__(self, provider: LLMProvider, model_name: str) -> None:
        self._provider = provider
        self.model_name = model_name

    def generate(self, inputs: list[tuple[Article, AiAnalysis]]) -> list[QuizItem]:
        if not inputs:
            return []
        generated: list[QuizItem] = []
        for article, analysis in inputs:
            if article.id is None:
                raise ValueError("quiz article must have a persisted id")
            article_input = {
                "article_id": article.id,
                "title": article.title,
                "summary": analysis.summary,
                "importance": analysis.importance,
                "attack_scenario": analysis.attack_scenario,
                "security_actions": analysis.security_actions or [],
                "key_concepts": analysis.key_concepts or [],
                "related_security_info": analysis.related_security_info or [],
            }
            payload = self._provider.generate_json(
                model=self.model_name,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=json.dumps(
                    {
                        "article": article_input,
                        "already_used_answers": [item.answer for item in generated],
                    },
                    ensure_ascii=False,
                ),
                schema=QuizTransportOutput.model_json_schema(),
                max_output_tokens=QUIZ_MAX_OUTPUT_TOKENS,
            )
            try:
                article_output = QuizOutput.model_validate(payload)
            except ValidationError as error:
                raise LLMResponseError("Quiz output validation failed") from error
            if len(article_output.quizzes) > 1:
                raise LLMResponseError("Quiz returned more than one item for an article")
            if any(item.article_id != article.id for item in article_output.quizzes):
                raise LLMResponseError("Quiz returned an unknown article_id")
            generated.extend(article_output.quizzes)

        try:
            output = QuizOutput.model_validate({"quizzes": generated})
        except ValidationError as error:
            raise LLMResponseError("Quiz output validation failed") from error
        return output.quizzes
