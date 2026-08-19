from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class QuizResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    article_id: int
    question: str


class QuizAnswerRequest(BaseModel):
    answer: str

    @field_validator("answer")
    @classmethod
    def reject_blank_answer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("answer must not be blank")
        return value


class QuizAnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str


class NewsInsightResponse(BaseModel):
    importance: str | None
    attack_scenario: str | None
    security_actions: list[str] | None
    key_concepts: list[dict[str, str]] | None
    related_security_info: list[dict[str, str]] | None


class NewsArticleResponse(BaseModel):
    id: int
    rank: int
    title: str
    url: str
    published_at: datetime
    summary: str | None
    insight: NewsInsightResponse


class NewsBriefingResponse(BaseModel):
    date: date
    count: int
    articles: list[NewsArticleResponse]


class NewsDateResponse(BaseModel):
    date: date
    article_count: int
