from pydantic import BaseModel, Field, model_validator


class SelectorDecision(BaseModel):
    article_id: int = Field(gt=0)
    rank: int = Field(ge=1, le=3)
    score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=1000)


class SelectorOutput(BaseModel):
    selections: list[SelectorDecision] = Field(max_length=3)

    @model_validator(mode="after")
    def validate_unique_items(self) -> "SelectorOutput":
        article_ids = [item.article_id for item in self.selections]
        ranks = [item.rank for item in self.selections]
        if len(article_ids) != len(set(article_ids)):
            raise ValueError("selected article_id values must be unique")
        if len(ranks) != len(set(ranks)):
            raise ValueError("selection ranks must be unique")
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise ValueError("selection ranks must be contiguous from 1")
        return self
