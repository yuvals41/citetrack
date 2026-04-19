from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResponseMentionType(str, Enum):
    MENTIONED = "mentioned"
    CITED = "cited"
    NOT_MENTIONED = "not_mentioned"


class ResponseCitation(BaseModel):
    url: str
    domain: str = ""


class AIResponseItem(BaseModel):
    id: str
    run_id: str
    provider: str
    model: str
    prompt_text: str
    response_text: str
    excerpt: str
    mention_type: ResponseMentionType
    citations: list[ResponseCitation] = Field(default_factory=list)
    position: int | None = None
    sentiment: str | None = None
    created_at: datetime


class AIResponsesList(BaseModel):
    workspace: str
    total: int
    items: list[AIResponseItem]
    degraded: dict[str, str] | None = None
