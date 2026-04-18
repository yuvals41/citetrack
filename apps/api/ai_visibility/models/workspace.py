"""Workspace domain model — multi-tenant scoping key."""

from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    """Request model for creating a workspace."""

    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-safe slug")
    description: str | None = Field(default=None, max_length=1000, description="Optional description")


class Workspace(BaseModel):
    """Full workspace model with ID and timestamps."""

    id: str = Field(..., description="Unique workspace ID")
    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-safe slug")
    description: str | None = Field(default=None, max_length=1000, description="Optional description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "ws_123",
                "name": "Acme Corp",
                "slug": "acme",
                "description": "Acme Corporation monitoring",
                "created_at": "2026-03-08T10:00:00",
                "updated_at": "2026-03-08T10:00:00",
            }
        }
