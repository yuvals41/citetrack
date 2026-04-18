"""Brand and Competitor domain models."""

from pydantic import BaseModel, Field


class Brand(BaseModel):
    """Brand model — the monitored entity."""

    id: str = Field(..., description="Unique brand ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    name: str = Field(..., min_length=1, max_length=255, description="Brand name")
    domain: str = Field(..., min_length=1, max_length=255, description="Primary domain")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "brand_123",
                "workspace_id": "ws_123",
                "name": "Acme",
                "domain": "acme.com",
            }
        }


class Competitor(BaseModel):
    """Competitor model — entities to compare against."""

    id: str = Field(..., description="Unique competitor ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    name: str = Field(..., min_length=1, max_length=255, description="Competitor name")
    domain: str = Field(..., min_length=1, max_length=255, description="Competitor domain")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "comp_123",
                "workspace_id": "ws_123",
                "name": "TechCorp",
                "domain": "techcorp.com",
            }
        }
