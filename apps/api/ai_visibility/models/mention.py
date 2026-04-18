"""Mention domain models — brand mentions and citations."""

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class MentionType(str, Enum):
    """Enum for mention types."""

    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    COMPARATIVE = "comparative"
    ABSENT = "absent"


class CitationRecord(BaseModel):
    """Citation record — proof of mention."""

    url: str | None = Field(default=None, description="URL where mention was found")
    domain: str | None = Field(default=None, description="Domain of the citation")
    status: Literal["found", "no_citation"] = Field(..., description="Citation status")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "domain": "example.com",
                "status": "found",
            }
        }


class Mention(BaseModel):
    """Mention model — a brand mention in LLM output."""

    id: str = Field(..., description="Unique mention ID")
    run_id: str = Field(..., description="Parent run ID")
    brand_id: str = Field(..., description="Brand being mentioned")
    mention_type: MentionType = Field(..., description="Type of mention")
    text: str = Field(..., min_length=1, description="Mention text excerpt")
    citation: CitationRecord = Field(..., description="Citation proof")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "mention_123",
                "run_id": "run_123",
                "brand_id": "brand_123",
                "mention_type": "explicit",
                "text": "Acme is a leader in...",
                "citation": {
                    "url": "https://example.com",
                    "domain": "example.com",
                    "status": "found",
                },
            }
        }
