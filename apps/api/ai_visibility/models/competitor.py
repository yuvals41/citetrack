from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def normalize_domain(value: str) -> str:
    return value.lower().strip().removeprefix("http://").removeprefix("https://").split("/")[0]


class CompetitorRecord(BaseModel):
    id: str
    workspace_id: str
    name: str
    domain: str
    created_at: datetime | None = None


class CompetitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=3, max_length=255)

    @field_validator("domain")
    @classmethod
    def normalize(cls, value: str) -> str:
        stripped = normalize_domain(value)
        if not re.match(r"^(?:[\w-]+\.)+[a-z]{2,}$", stripped):
            raise ValueError("Invalid domain format")
        return stripped


class CompetitorListResponse(BaseModel):
    workspace: str
    items: list[CompetitorRecord]
    degraded: dict[str, str] | None = None
