from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class KeyConcept(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)


class RelatedSecurityInfo(BaseModel):
    type: Literal["CVE", "TECHNIQUE", "PRODUCT", "VULNERABILITY", "TECHNOLOGY"]
    value: str = Field(min_length=1, max_length=300)


class AnalystOutput(BaseModel):
    importance: str = Field(min_length=1, max_length=3000)
    attack_scenario: str = Field(min_length=1, max_length=4000)
    security_actions: list[str] = Field(max_length=5)
    key_concepts: list[KeyConcept] = Field(max_length=5)
    related_security_info: list[RelatedSecurityInfo] = Field(max_length=5)

    @field_validator("importance", "attack_scenario")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("security_actions")
    @classmethod
    def clean_actions(cls, values: list[str]) -> list[str]:
        cleaned = [" ".join(value.split()) for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))

    @model_validator(mode="after")
    def deduplicate_structured_items(self) -> "AnalystOutput":
        concepts: dict[str, KeyConcept] = {}
        for item in self.key_concepts:
            item.name = item.name.strip()
            item.description = " ".join(item.description.split())
            if item.name and item.description:
                concepts.setdefault(item.name.casefold(), item)
        related: dict[tuple[str, str], RelatedSecurityInfo] = {}
        for item in self.related_security_info:
            item.value = " ".join(item.value.split())
            if item.value:
                related.setdefault((item.type, item.value.casefold()), item)
        self.key_concepts = list(concepts.values())
        self.related_security_info = list(related.values())
        return self
