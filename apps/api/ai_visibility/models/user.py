"""User models for authenticated API endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime | None = None


class UserCreate(BaseModel):
    user_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserResponse(BaseModel):
    user_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    workspace_count: int = 0
    has_completed_onboarding: bool = False
