from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class DegradedPayload(BaseModel):
    reason: str
    message: str


class UrlRequest(BaseModel):
    url: HttpUrl


class QueryFanoutRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    brand_domain: str = Field(min_length=1, max_length=255)


class BrandRequest(BaseModel):
    brand_name: str = Field(min_length=1, max_length=255)


class AnalyzerDimension(BaseModel):
    score: int = Field(ge=0, le=100)
    finding: str


class ExtractabilityResult(BaseModel):
    url: str
    overall_score: float = Field(ge=0, le=100)
    summary_block: AnalyzerDimension
    section_integrity: AnalyzerDimension
    modular_content: AnalyzerDimension
    schema_markup: AnalyzerDimension
    static_content: AnalyzerDimension
    recommendations: list[str] = Field(default_factory=list)
    degraded: dict[str, str] | None = None


class BotAccessResult(BaseModel):
    bot: str
    accessible: bool
    status_code: int
    reason: str


class CrawlerSimResult(BaseModel):
    url: str
    results: list[BotAccessResult]
    degraded: dict[str, str] | None = None


class QueryFanoutItem(BaseModel):
    sub_query: str
    ranked: bool
    position: int | None = None


class QueryFanoutResult(BaseModel):
    fanout_prompt: str
    results: list[QueryFanoutItem] = Field(default_factory=list)
    coverage: float = Field(ge=0, le=1)
    degraded: dict[str, str] | None = None


class PresenceResult(BaseModel):
    present: bool
    url: str | None = None


class EntityResult(BaseModel):
    brand_name: str
    entity_clarity_score: float = Field(ge=0, le=1)
    knowledge_graph: PresenceResult
    wikipedia: PresenceResult
    wikidata: PresenceResult
    recommendations: list[str] = Field(default_factory=list)
    degraded: dict[str, str] | None = None


class GoogleShoppingResult(BaseModel):
    brand_products_found: bool


class AIShoppingResult(BaseModel):
    brand_in_ai_text: bool


class ChatGPTShoppingResult(BaseModel):
    brand_mentioned: bool


class ShoppingResult(BaseModel):
    brand_name: str
    visibility_score: float = Field(ge=0, le=1)
    google_shopping: GoogleShoppingResult
    ai_mode_shopping: AIShoppingResult
    chatgpt_shopping: ChatGPTShoppingResult
    recommendations: list[str] = Field(default_factory=list)
    degraded: dict[str, str] | None = None
