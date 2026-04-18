"""Prompt domain models — prompts, versions, and sets."""

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    """Prompt model — a single prompt template."""

    id: str = Field(..., description="Unique prompt ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    name: str = Field(..., min_length=1, max_length=255, description="Prompt name")
    text: str = Field(..., min_length=1, description="Prompt text/template")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "prompt_123",
                "workspace_id": "ws_123",
                "name": "Market Analysis",
                "text": "Analyze the market for...",
            }
        }


class PromptVersion(BaseModel):
    """PromptVersion model — versioned prompt history."""

    id: str = Field(..., description="Unique version ID")
    prompt_id: str = Field(..., description="Parent prompt ID")
    version: int = Field(..., ge=1, description="Version number (1-indexed)")
    text: str = Field(..., min_length=1, description="Prompt text at this version")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "pv_123",
                "prompt_id": "prompt_123",
                "version": 1,
                "text": "Analyze the market for...",
            }
        }


class PromptSet(BaseModel):
    """PromptSet model — grouping of prompts for batch runs."""

    id: str = Field(..., description="Unique prompt set ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    name: str = Field(..., min_length=1, max_length=255, description="Set name")
    prompt_ids: list[str] = Field(..., description="List of prompt IDs in this set")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "ps_123",
                "workspace_id": "ws_123",
                "name": "Q1 Analysis",
                "prompt_ids": ["prompt_123", "prompt_456"],
            }
        }
