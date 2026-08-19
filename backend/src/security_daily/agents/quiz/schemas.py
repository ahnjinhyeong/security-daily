from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


def normalize(value: str) -> str:
    return " ".join(value.split()).casefold()


class QuizItem(BaseModel):
    article_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(min_length=1, max_length=200)
    accepted_answers: list[str] = Field(max_length=10)
    explanation: str = Field(min_length=1, max_length=2000)

    @field_validator("question", "answer", "explanation")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("accepted_answers")
    @classmethod
    def clean_accepted_answers(cls, values: list[str]) -> list[str]:
        result: dict[str, str] = {}
        for value in values:
            cleaned = " ".join(value.split())
            if cleaned:
                result.setdefault(normalize(cleaned), cleaned)
        return list(result.values())


class QuizOutput(BaseModel):
    quizzes: list[QuizItem] = Field(max_length=3)

    @model_validator(mode="after")
    def reject_duplicate_questions_and_concepts(self) -> "QuizOutput":
        questions = [normalize(item.question) for item in self.quizzes]
        answers = [normalize(item.answer) for item in self.quizzes]
        if len(questions) != len(set(questions)):
            raise ValueError("quiz questions must be unique")
        if len(answers) != len(set(answers)):
            raise ValueError("quiz core answers must be unique")
        for item in self.quizzes:
            canonical = normalize(item.answer)
            item.accepted_answers = [
                value for value in item.accepted_answers if normalize(value) != canonical
            ]
        return self


class QuizTransportItem(BaseModel):
    article_id: int
    question: str = Field(max_length=100)
    answer: str = Field(max_length=30)
    accepted_answers: list[Annotated[str, Field(max_length=30)]] = Field(max_length=3)
    explanation: str = Field(max_length=200)


class QuizTransportOutput(BaseModel):
    quizzes: list[QuizTransportItem] = Field(max_length=1)
