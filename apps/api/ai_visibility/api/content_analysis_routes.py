from __future__ import annotations

from fastapi import APIRouter
from loguru import logger

from ai_visibility.api.auth import CurrentUserId
from ai_visibility.models.content_analysis import (
    AIShoppingResult,
    AnalyzerDimension,
    BrandRequest,
    ChatGPTShoppingResult,
    CrawlerSimResult,
    EntityResult,
    ExtractabilityResult,
    GoogleShoppingResult,
    PresenceResult,
    QueryFanoutRequest,
    QueryFanoutResult,
    ShoppingResult,
    UrlRequest,
)
from ai_visibility.services.content_analysis import (
    analyze_brand_entity,
    analyze_extractability,
    analyze_shopping_visibility,
    generate_query_fanout,
    simulate_crawler_access,
)

router = APIRouter(tags=["content-analysis"])


@router.post("/analyzers/extractability", response_model=ExtractabilityResult)
async def run_extractability(request: UrlRequest, user_id: CurrentUserId) -> ExtractabilityResult:
    _ = user_id
    try:
        return await analyze_extractability(str(request.url))
    except Exception as exc:  # noqa: BLE001
        logger.exception("content_analysis.extractability.failed url={} error={}", request.url, exc)
        return ExtractabilityResult(
            url=str(request.url),
            overall_score=0,
            summary_block=AnalyzerDimension(score=0, finding="Analysis failed."),
            section_integrity=AnalyzerDimension(score=0, finding="Analysis failed."),
            modular_content=AnalyzerDimension(score=0, finding="Analysis failed."),
            schema_markup=AnalyzerDimension(score=0, finding="Analysis failed."),
            static_content=AnalyzerDimension(score=0, finding="Analysis failed."),
            recommendations=[],
            degraded={"reason": "analysis_failed", "message": str(exc)},
        )


@router.post("/analyzers/crawler-sim", response_model=CrawlerSimResult)
async def run_crawler_sim(request: UrlRequest, user_id: CurrentUserId) -> CrawlerSimResult:
    _ = user_id
    try:
        return await simulate_crawler_access(str(request.url))
    except Exception as exc:  # noqa: BLE001
        logger.exception("content_analysis.crawler_sim.failed url={} error={}", request.url, exc)
        return CrawlerSimResult(
            url=str(request.url),
            results=[],
            degraded={"reason": "analysis_failed", "message": str(exc)},
        )


@router.post("/analyzers/query-fanout", response_model=QueryFanoutResult)
async def run_query_fanout(request: QueryFanoutRequest, user_id: CurrentUserId) -> QueryFanoutResult:
    _ = user_id
    try:
        return await generate_query_fanout(request.prompt, request.brand_domain)
    except Exception as exc:  # noqa: BLE001
        logger.exception("content_analysis.query_fanout.failed domain={} error={}", request.brand_domain, exc)
        return QueryFanoutResult(
            fanout_prompt=request.prompt,
            results=[],
            coverage=0,
            degraded={"reason": "analysis_failed", "message": str(exc)},
        )


@router.post("/analyzers/entity", response_model=EntityResult)
async def run_entity_analysis(request: BrandRequest, user_id: CurrentUserId) -> EntityResult:
    _ = user_id
    try:
        return await analyze_brand_entity(request.brand_name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("content_analysis.entity.failed brand={} error={}", request.brand_name, exc)
        return EntityResult(
            brand_name=request.brand_name,
            entity_clarity_score=0,
            knowledge_graph=PresenceResult(present=False, url=None),
            wikipedia=PresenceResult(present=False, url=None),
            wikidata=PresenceResult(present=False, url=None),
            recommendations=[],
            degraded={"reason": "analysis_failed", "message": str(exc)},
        )


@router.post("/analyzers/shopping", response_model=ShoppingResult)
async def run_shopping_analysis(request: BrandRequest, user_id: CurrentUserId) -> ShoppingResult:
    _ = user_id
    try:
        return await analyze_shopping_visibility(request.brand_name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("content_analysis.shopping.failed brand={} error={}", request.brand_name, exc)
        return ShoppingResult(
            brand_name=request.brand_name,
            visibility_score=0,
            google_shopping=GoogleShoppingResult(brand_products_found=False),
            ai_mode_shopping=AIShoppingResult(brand_in_ai_text=False),
            chatgpt_shopping=ChatGPTShoppingResult(brand_mentioned=False),
            recommendations=[],
            degraded={"reason": "analysis_failed", "message": str(exc)},
        )
