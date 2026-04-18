"""Onboarding request and response models."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator


def _normalize_domain(value: str) -> str:
    stripped = value.strip().lower().removeprefix("http://").removeprefix("https://")
    if not re.match(r"^(?:[\w-]+\.)+[a-z]{2,}(?:/.*)?$", stripped):
        raise ValueError("Invalid domain format")
    return stripped


class OnboardingEngine(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    XAI = "xai"


class OnboardingBrand(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=3, max_length=255)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        return _normalize_domain(value)


class OnboardingCompetitor(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=3, max_length=255)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        return _normalize_domain(value)


class OnboardingPayload(BaseModel):
    brand: OnboardingBrand
    competitors: list[OnboardingCompetitor] = Field(max_length=5)
    engines: list[OnboardingEngine] = Field(min_length=1)


class OnboardingCompleteResponse(BaseModel):
    workspace_slug: str
