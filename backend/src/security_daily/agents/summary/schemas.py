import re

from pydantic import BaseModel, Field, field_validator


class SummaryOutput(BaseModel):
    summary: str = Field(min_length=1, max_length=3000)

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        sentences = [part for part in re.split(r"(?<=[.!?。])\s+", cleaned) if part]
        if len(sentences) > 5:
            raise ValueError("summary must contain at most 5 sentences")
        return cleaned
