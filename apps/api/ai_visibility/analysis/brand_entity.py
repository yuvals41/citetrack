# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAny=false, reportUnusedCallResult=false, reportMissingTypeArgument=false, reportUnknownParameterType=false, reportExplicitAny=false, reportImplicitStringConcatenation=false
import asyncio
import os
from typing import Any, TypedDict, cast
from urllib.parse import quote, urlparse

import httpx
from loguru import logger

KG_URL = "https://kgsearch.googleapis.com/v1/entities:search"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
TIMEOUT = 20.0
_HTTP_HEADERS = {
    "User-Agent": "AIVisibility/1.0 (https://solaraai.com; contact@solaraai.com)",
    "Accept": "application/json",
}


class KnowledgeGraphMatch(TypedDict):
    entity_id: object
    name: object
    types: list[object]
    description: object
    result_score: float
    url: object
    wikipedia_url: object
    domain_match: bool


def _normalize_domain(domain: str) -> str:
    cleaned = domain.strip().lower()
    if not cleaned:
        return ""
    if "://" not in cleaned:
        cleaned = f"https://{cleaned}"
    parsed = urlparse(cleaned)
    host = parsed.netloc or parsed.path
    if host.startswith("www."):
        host = host[4:]
    return host.split("/")[0]


def _base_kg_result() -> dict[str, Any]:
    return {
        "present": False,
        "entity_id": None,
        "result_score": 0.0,
        "correct_entity": False,
        "description": None,
        "types": [],
    }


def _base_wikidata_result() -> dict[str, Any]:
    return {
        "present": False,
        "entity_id": None,
        "description": None,
        "sitelinks_count": 0,
    }


def _base_wikipedia_result() -> dict[str, Any]:
    return {
        "present": False,
        "title": None,
        "description": None,
        "extract": None,
    }


async def _fetch_knowledge_graph(brand_name: str, domain: str) -> dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        logger.debug("[entity] GOOGLE_API_KEY missing, skipping Knowledge Graph check")
        return _base_kg_result()

    params: dict[str, str | int] = {
        "query": brand_name,
        "types": "Organization",
        "key": api_key,
        "languages": "en",
        "limit": 5,
    }
    normalized_domain = _normalize_domain(domain)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=_HTTP_HEADERS) as client:
        response = await client.get(KG_URL, params=params)
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())

    item_list = payload.get("itemListElement", [])
    if not isinstance(item_list, list) or not item_list:
        return _base_kg_result()

    best_match: KnowledgeGraphMatch | None = None
    fallback_match: KnowledgeGraphMatch | None = None

    for raw_item in item_list:
        if not isinstance(raw_item, dict):
            continue
        result = raw_item.get("result", {})
        if not isinstance(result, dict):
            continue

        url = str(result.get("url", "")).lower()
        domain_match = bool(normalized_domain and normalized_domain in url)
        parsed_item: KnowledgeGraphMatch = {
            "entity_id": result.get("@id"),
            "name": result.get("name"),
            "types": cast(list[object], result.get("@type")) if isinstance(result.get("@type"), list) else [],
            "description": result.get("description"),
            "result_score": float(raw_item.get("resultScore", 0.0) or 0.0),
            "url": result.get("url"),
            "wikipedia_url": (
                result.get("detailedDescription", {}).get("url")
                if isinstance(result.get("detailedDescription"), dict)
                else None
            ),
            "domain_match": domain_match,
        }

        if domain_match and best_match is None:
            best_match = parsed_item
        if fallback_match is None:
            fallback_match = parsed_item

    selected = best_match or fallback_match
    if not selected:
        return _base_kg_result()

    return {
        "present": True,
        "entity_id": selected.get("entity_id"),
        "result_score": float(selected.get("result_score", 0.0)),
        "correct_entity": bool(selected.get("domain_match", False)),
        "description": selected.get("description"),
        "types": selected.get("types", []),
    }


async def _fetch_wikidata(brand_name: str) -> dict[str, Any]:
    params: dict[str, str | int] = {
        "action": "wbsearchentities",
        "search": brand_name,
        "language": "en",
        "type": "item",
        "limit": 5,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=_HTTP_HEADERS) as client:
        search_resp = await client.get(WIKIDATA_SEARCH_URL, params=params)
        search_resp.raise_for_status()
        search_payload = cast(dict[str, Any], search_resp.json())

        search_results = search_payload.get("search", [])
        if not isinstance(search_results, list) or not search_results:
            return _base_wikidata_result()

        first = search_results[0]
        if not isinstance(first, dict):
            return _base_wikidata_result()

        entity_id = str(first.get("id", "")).strip()
        if not entity_id:
            return _base_wikidata_result()

        entity_resp = await client.get(f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json")
        entity_resp.raise_for_status()
        entity_payload = cast(dict[str, Any], entity_resp.json())

    entities = entity_payload.get("entities", {})
    entity = entities.get(entity_id, {}) if isinstance(entities, dict) else {}
    sitelinks = entity.get("sitelinks", {}) if isinstance(entity, dict) else {}
    sitelinks_count = len(sitelinks) if isinstance(sitelinks, dict) else 0

    has_enwiki = isinstance(sitelinks, dict) and "enwiki" in sitelinks
    if has_enwiki and sitelinks_count == 0:
        sitelinks_count = 1

    return {
        "present": True,
        "entity_id": entity_id,
        "description": first.get("description"),
        "sitelinks_count": sitelinks_count,
    }


async def _fetch_wikipedia(brand_name: str) -> dict[str, Any]:
    page_name = quote(brand_name, safe="")
    url = f"{WIKIPEDIA_SUMMARY_URL}/{page_name}"

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=_HTTP_HEADERS) as client:
        response = await client.get(url)
        if response.status_code == 404:
            return _base_wikipedia_result()
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())

    return {
        "present": True,
        "title": payload.get("title"),
        "description": payload.get("description"),
        "extract": payload.get("extract"),
    }


def _compute_entity_clarity_score(
    kg: dict[str, Any],
    wikidata: dict[str, Any],
    wikipedia: dict[str, Any],
) -> float:
    score = 0.0

    if kg.get("present"):
        score += 0.25
    if float(kg.get("result_score", 0.0) or 0.0) > 500:
        score += 0.15
    if kg.get("correct_entity"):
        score += 0.10

    if wikidata.get("present"):
        score += 0.15
    if wikipedia.get("present"):
        score += 0.20

    sitelinks_count = int(wikidata.get("sitelinks_count", 0) or 0)
    if sitelinks_count > 10:
        score += 0.10
    if sitelinks_count > 20:
        score += 0.05

    return round(min(score, 1.0), 4)


def _build_recommendations(kg: dict[str, Any], wikidata: dict[str, Any], wikipedia: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []

    if not kg.get("present"):
        recommendations.append(
            "Create/claim your Google Business Profile and ensure consistent brand info across the web"
        )
    if not wikipedia.get("present"):
        recommendations.append(
            "Your brand lacks a Wikipedia page — contribute to relevant Wikipedia articles and build notability"
        )
    if kg.get("present") and float(kg.get("result_score", 0.0) or 0.0) <= 500:
        recommendations.append(
            "Strengthen your brand's online presence with consistent NAP data and structured data markup"
        )
    if not wikidata.get("present"):
        recommendations.append("Create a Wikidata entry for your brand to improve entity recognition")
    if kg.get("present") and not kg.get("correct_entity"):
        recommendations.append(
            "Your brand name may be ambiguous — consider adding disambiguation through schema.org markup"
        )

    return recommendations


async def analyze_brand_entity(brand_name: str, domain: str) -> dict[str, Any]:
    clean_brand = brand_name.strip()
    if not clean_brand:
        logger.debug("[entity] Empty brand name received")
        return {
            "brand": brand_name,
            "entity_clarity_score": 0.0,
            "knowledge_graph": _base_kg_result(),
            "wikidata": _base_wikidata_result(),
            "wikipedia": _base_wikipedia_result(),
            "recommendations": [
                "Create/claim your Google Business Profile and ensure consistent brand info across the web",
                "Your brand lacks a Wikipedia page — contribute to relevant Wikipedia articles and build notability",
                "Create a Wikidata entry for your brand to improve entity recognition",
            ],
        }

    logger.debug(f"[entity] Starting brand entity analysis for '{clean_brand}'")

    results = await asyncio.gather(
        _fetch_knowledge_graph(clean_brand, domain),
        _fetch_wikidata(clean_brand),
        _fetch_wikipedia(clean_brand),
        return_exceptions=True,
    )

    kg_result = _base_kg_result()
    wikidata_result = _base_wikidata_result()
    wikipedia_result = _base_wikipedia_result()

    if isinstance(results[0], Exception):
        logger.debug(f"[entity] Knowledge Graph lookup failed: {type(results[0]).__name__}: {results[0]}")
    else:
        kg_result = cast(dict[str, Any], results[0])

    if isinstance(results[1], Exception):
        logger.debug(f"[entity] Wikidata lookup failed: {type(results[1]).__name__}: {results[1]}")
    else:
        wikidata_result = cast(dict[str, Any], results[1])

    if isinstance(results[2], Exception):
        logger.debug(f"[entity] Wikipedia lookup failed: {type(results[2]).__name__}: {results[2]}")
    else:
        wikipedia_result = cast(dict[str, Any], results[2])

    score = _compute_entity_clarity_score(kg_result, wikidata_result, wikipedia_result)
    recommendations = _build_recommendations(kg_result, wikidata_result, wikipedia_result)

    logger.debug(
        f"[entity] Completed brand entity analysis | brand={clean_brand} "
        f"score={score} kg_present={kg_result['present']} "
        f"wikidata_present={wikidata_result['present']} wikipedia_present={wikipedia_result['present']}"
    )

    return {
        "brand": clean_brand,
        "entity_clarity_score": score,
        "knowledge_graph": kg_result,
        "wikidata": wikidata_result,
        "wikipedia": wikipedia_result,
        "recommendations": recommendations,
    }
