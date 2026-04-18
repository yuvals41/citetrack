"""Metric domain models — visibility scores and comparisons."""

from pydantic import BaseModel, Field


class MetricSnapshot(BaseModel):
    """MetricSnapshot model — visibility metrics at a point in time."""

    id: str = Field(..., description="Unique metric snapshot ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    brand_id: str = Field(..., description="Brand ID")
    formula_version: str = Field(..., min_length=1, description="Formula version (immutable for history)")
    visibility_score: float = Field(..., ge=0.0, le=100.0, description="Visibility score 0-100")
    mention_count: int = Field(..., ge=0, description="Total mention count")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "metric_123",
                "workspace_id": "ws_123",
                "brand_id": "brand_123",
                "formula_version": "v1.0",
                "visibility_score": 85.5,
                "mention_count": 42,
            }
        }


class CompetitorComparison(BaseModel):
    """CompetitorComparison model — relative metrics vs competitors."""

    id: str = Field(..., description="Unique comparison ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    brand_id: str = Field(..., description="Brand ID")
    competitor_id: str = Field(..., description="Competitor ID")
    visibility_delta: float = Field(..., description="Visibility score difference (brand - competitor)")
    mention_delta: int = Field(..., description="Mention count difference (brand - competitor)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "comp_123",
                "workspace_id": "ws_123",
                "brand_id": "brand_123",
                "competitor_id": "comp_456",
                "visibility_delta": 5.2,
                "mention_delta": 3,
            }
        }
