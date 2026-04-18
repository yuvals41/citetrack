from __future__ import annotations

import re

from loguru import logger

from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository


def _build_candidate_terms(workspace_slug: str, brand_name: str) -> set[str]:
    brand_slug = workspace_slug.lower()
    terms = {
        term.lower()
        for term in (
            brand_slug,
            brand_slug.replace("-", " "),
            brand_slug.replace("_", " "),
            brand_name.lower(),
        )
        if term
    }
    slug_lower = brand_slug.replace("-", "").replace("_", "")
    for i in range(2, len(slug_lower) - 1):
        left = slug_lower[:i]
        right = slug_lower[i:]
        if len(left) >= 2 and len(right) >= 2:
            terms.add(f"{left} {right}")
    return terms


async def compute_competitor_scores(workspace_slug: str) -> list[dict[str, str]]:
    """Compute competitor scores from existing scan data."""
    try:
        prisma = await get_prisma()
        ws = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
        if ws is None:
            return [
                {
                    "name": workspace_slug,
                    "score": "0.00",
                    "is_brand": "true",
                }
            ]

        workspace_id = ws["id"]
        brand_name = str(ws.get("brand_name") or workspace_slug)
        candidate_terms = _build_candidate_terms(workspace_slug, brand_name)
        brand_slug = workspace_slug.lower()

        latest_prompt_rows = await prisma.query_raw(
            """
            WITH latest_executions AS (
                SELECT DISTINCT ON (se.provider)
                    se.id,
                    se.provider,
                    se.executed_at
                FROM ai_vis_scan_executions se
                JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
                WHERE sj.workspace_slug = $1
                ORDER BY se.provider, se.executed_at DESC, se.id DESC
            )
            SELECT pe.raw_response
            FROM ai_vis_prompt_executions pe
            JOIN latest_executions le ON le.id = pe.scan_execution_id
            ORDER BY le.provider, pe.executed_at ASC, pe.id ASC
            """,
            workspace_slug,
        )

        type_counts = {"explicit": 0, "citation": 0, "absent": 0}
        response_lowers: list[str] = []
        if isinstance(latest_prompt_rows, list):
            for row in latest_prompt_rows:
                if not isinstance(row, dict):
                    continue
                raw_response = str(row.get("raw_response") or "")
                response_lower = raw_response.lower()
                response_lowers.append(response_lower)

                is_explicit = any(term in response_lower for term in candidate_terms)
                all_urls = re.findall(r"https?://[^\s\)\]\}>,\"']+", raw_response)
                brand_cited = any(
                    brand_slug in url.lower() or brand_slug.replace("-", "") in url.lower() for url in all_urls
                )

                if brand_cited:
                    mention_type = "citation"
                elif is_explicit:
                    mention_type = "explicit"
                else:
                    mention_type = "absent"
                type_counts[mention_type] = type_counts.get(mention_type, 0) + 1

        total_responses = sum(type_counts.values())
        brand_mentions = type_counts.get("explicit", 0) + type_counts.get("citation", 0)
        brand_visibility = round(brand_mentions / total_responses, 2) if total_responses > 0 else 0.0

        competitor_scores: list[dict[str, str]] = [
            {
                "name": workspace_slug,
                "score": f"{brand_visibility:.2f}",
                "is_brand": "true",
            }
        ]

        competitors_raw = await prisma.query_raw(
            'SELECT "name" FROM "ai_vis_competitors" WHERE "workspace_id" = $1',
            workspace_id,
        )
        if isinstance(competitors_raw, list):
            for competitor in competitors_raw:
                if not isinstance(competitor, dict):
                    continue
                raw_name = str(competitor.get("name") or "").strip()
                if not raw_name:
                    continue
                competitor_name = raw_name.split("(")[0].strip()
                if not competitor_name:
                    continue
                competitor_lower = competitor_name.lower()
                mention_count = sum(1 for response in response_lowers if competitor_lower in response)
                competitor_visibility = round(mention_count / total_responses, 2) if total_responses > 0 else 0.0
                competitor_scores.append(
                    {
                        "name": competitor_name,
                        "score": f"{competitor_visibility:.2f}",
                        "is_brand": "false",
                    }
                )

        return competitor_scores
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"[competitor_service] failed for {workspace_slug}: {type(exc).__name__}: {exc}")
        return [
            {
                "name": workspace_slug,
                "score": "0.00",
                "is_brand": "true",
            }
        ]
