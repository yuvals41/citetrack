from typing import Literal

from pydantic import BaseModel, Field


class MentionResult(BaseModel):
    brand_name: str
    mentioned: bool
    sentiment: Literal["positive", "neutral", "negative", "unknown"] = "unknown"
    context_snippet: str | None = None
    position_in_response: int | None = None


class CitationResult(BaseModel):
    url: str | None = None
    domain: str | None = None
    status: Literal["found", "no_citation"] = "no_citation"


class ParseResult(BaseModel):
    parser_status: Literal["parsed", "fallback", "failed"]
    parser_version: str = "1.0.0"
    mentions: list[MentionResult] = Field(default_factory=list)
    citations: list[CitationResult] = Field(default_factory=list)
    raw_text: str | None = None
    error_message: str | None = None
