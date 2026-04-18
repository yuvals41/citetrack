"""Recommendation domain models — actionable insights."""

from pydantic import BaseModel, Field


class RuleTrigger(BaseModel):
    """RuleTrigger model — rule that triggered a recommendation."""

    id: str = Field(..., description="Unique trigger ID")
    rule_name: str = Field(..., min_length=1, description="Name of the rule")
    threshold: float = Field(..., description="Threshold value")
    current_value: float = Field(..., description="Current value that triggered rule")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "trigger_123",
                "rule_name": "low_visibility",
                "threshold": 50.0,
                "current_value": 45.5,
            }
        }


class Recommendation(BaseModel):
    """Recommendation model — actionable insight for user."""

    id: str = Field(..., description="Unique recommendation ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    brand_id: str = Field(..., description="Brand ID")
    title: str = Field(..., min_length=1, max_length=255, description="Recommendation title")
    description: str = Field(..., min_length=1, description="Detailed description")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    rule_triggers: list[RuleTrigger] = Field(default_factory=list, description="Rules that triggered this")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "rec_123",
                "workspace_id": "ws_123",
                "brand_id": "brand_123",
                "title": "Increase content marketing",
                "description": "Your visibility is below competitors",
                "priority": "high",
                "rule_triggers": [
                    {
                        "id": "trigger_123",
                        "rule_name": "low_visibility",
                        "threshold": 50.0,
                        "current_value": 45.5,
                    }
                ],
            }
        }
