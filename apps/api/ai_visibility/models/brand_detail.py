from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from ai_visibility.models.competitor import normalize_domain


def _validate_domain(value: str) -> str:
    stripped: str = normalize_domain(value)
    if not re.match(r"^(?:[\w-]+\.)+[a-z]{2,}$", stripped):
        raise ValueError("Invalid domain format")
    return stripped


class BrandDetail(BaseModel):
    id: str
    workspace_id: str
    name: str
    domain: str
    aliases: list[str] = Field(default_factory=list)
    degraded: dict[str, str] | None = None


BrandRecord = BrandDetail


class BrandUpsertInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=3, max_length=255)
    aliases: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        return _validate_domain(value)

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, value: list[str]) -> list[str]:
        cleaned = [alias.strip() for alias in value if alias.strip()]
        if len(cleaned) > 10:
            raise ValueError("No more than 10 aliases are allowed")
        return cleaned
