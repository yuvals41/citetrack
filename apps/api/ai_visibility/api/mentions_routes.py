from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportCallInDefaultInitializer=false

from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import urlparse

from fastapi import APIRouter, Query
from loguru import logger

from ai_visibility.api.auth import CurrentUserId
from ai_visibility.models.response_view import (
    AIResponseItem,
    AIResponsesList,
    ResponseCitation,
    ResponseMentionType,
)
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

router = APIRouter(tags=["responses"])


def _as_mapping(row: object) -> Mapping[str, object] | None:
    if isinstance(row, Mapping):
        return cast(Mapping[str, object], row)
    return None


def _excerpt(response_text: str) -> str:
    return response_text[:200]


def _domain_from_url(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:  # noqa: BLE001
        return ""
    return domain[4:] if domain.startswith("www.") else domain


def _to_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _mention_type(
    observation: Mapping[str, object] | None,
    citations: list[ResponseCitation],
) -> ResponseMentionType:
    if observation is None:
        return ResponseMentionType.NOT_MENTIONED

    brand_mentioned = bool(observation.get("brand_mentioned"))
    if not brand_mentioned:
        return ResponseMentionType.NOT_MENTIONED
    if citations:
        return ResponseMentionType.CITED
    return ResponseMentionType.MENTIONED


def _degraded_payload(workspace_slug: str, exc: Exception) -> AIResponsesList:
    logger.exception("responses.list.failed workspace={} error={}", workspace_slug, exc)
    return AIResponsesList(
        workspace=workspace_slug,
        total=0,
        items=[],
        degraded={
            "reason": "provider_failure",
            "message": f"AI responses are temporarily unavailable: {exc}",
        },
    )


@router.get("/workspaces/{workspace_slug}/responses", response_model=AIResponsesList)
async def list_workspace_responses(
    workspace_slug: str,
    user_id: CurrentUserId,
    run_id: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> AIResponsesList:
    _ = user_id

    try:
        prisma = await get_prisma()
        workspace = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
        if workspace is None:
            return AIResponsesList(workspace=workspace_slug, total=0, items=[])

        total_params: list[object] = [workspace_slug]
        items_params: list[object] = [workspace_slug]
        run_filter_sql = ""
        if run_id:
            run_filter_sql = " AND se.id = $2"
            total_params.append(run_id)
            items_params.append(run_id)

        limit_index = len(items_params) + 1
        offset_index = limit_index + 1
        items_params.extend([limit, offset])

        total_rows = await prisma.query_raw(
            f"""
            SELECT COUNT(*) AS total
            FROM ai_vis_prompt_executions pe
            JOIN ai_vis_scan_executions se ON se.id = pe.scan_execution_id
            JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
            WHERE sj.workspace_slug = $1{run_filter_sql}
            """,
            *total_params,
        )

        prompt_rows = await prisma.query_raw(
            f"""
            SELECT pe.id,
                   pe.scan_execution_id AS run_id,
                   se.provider,
                   se.model_name AS model,
                   pe.prompt_text,
                   pe.raw_response AS response_text,
                   pe.executed_at AS created_at
            FROM ai_vis_prompt_executions pe
            JOIN ai_vis_scan_executions se ON se.id = pe.scan_execution_id
            JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
            WHERE sj.workspace_slug = $1{run_filter_sql}
            ORDER BY pe.executed_at DESC, pe.id DESC
            LIMIT ${limit_index} OFFSET ${offset_index}
            """,
            *items_params,
        )

        total_row = _as_mapping(total_rows[0]) if isinstance(total_rows, list) and total_rows else None
        total = _to_int(total_row.get("total") if total_row is not None else 0)

        response_rows: list[Mapping[str, object]] = []
        if isinstance(prompt_rows, list):
            response_rows = [row for row in (_as_mapping(item) for item in prompt_rows) if row is not None]

        prompt_execution_ids = [str(row.get("id") or "") for row in response_rows if str(row.get("id") or "")]

        citations_by_execution: dict[str, list[ResponseCitation]] = {}
        observations_by_execution: dict[str, Mapping[str, object]] = {}

        if prompt_execution_ids:
            citation_rows = await prisma.query_raw(
                """
                SELECT prompt_execution_id, url
                FROM ai_vis_prompt_execution_citations
                WHERE prompt_execution_id = ANY($1::text[])
                ORDER BY prompt_execution_id ASC, id ASC
                """,
                prompt_execution_ids,
            )
            if isinstance(citation_rows, list):
                for item in citation_rows:
                    row = _as_mapping(item)
                    if row is None:
                        continue
                    execution_id = str(row.get("prompt_execution_id") or "")
                    url = str(row.get("url") or "")
                    if not execution_id or not url:
                        continue
                    citations_by_execution.setdefault(execution_id, []).append(
                        ResponseCitation(url=url, domain=_domain_from_url(url))
                    )

            observation_rows = await prisma.query_raw(
                """
                SELECT prompt_execution_id,
                       brand_mentioned,
                       brand_position
                FROM ai_vis_observations
                WHERE prompt_execution_id = ANY($1::text[])
                ORDER BY prompt_execution_id ASC, brand_mentioned DESC, brand_position ASC NULLS LAST, id ASC
                """,
                prompt_execution_ids,
            )
            if isinstance(observation_rows, list):
                for item in observation_rows:
                    row = _as_mapping(item)
                    if row is None:
                        continue
                    execution_id = str(row.get("prompt_execution_id") or "")
                    if execution_id and execution_id not in observations_by_execution:
                        observations_by_execution[execution_id] = row

        items: list[AIResponseItem] = []
        for row in response_rows:
            execution_id = str(row.get("id") or "")
            response_text = str(row.get("response_text") or "")
            citations = citations_by_execution.get(execution_id, [])
            observation = observations_by_execution.get(execution_id)
            items.append(
                AIResponseItem(
                    id=execution_id,
                    run_id=str(row.get("run_id") or ""),
                    provider=str(row.get("provider") or ""),
                    model=str(row.get("model") or ""),
                    prompt_text=str(row.get("prompt_text") or ""),
                    response_text=response_text,
                    excerpt=_excerpt(response_text),
                    mention_type=_mention_type(observation, citations),
                    citations=citations,
                    position=(
                        _to_int(observation.get("brand_position"))
                        if observation is not None and observation.get("brand_position") is not None
                        else None
                    ),
                    sentiment=None,
                    created_at=cast(Any, row.get("created_at")),
                )
            )

        return AIResponsesList(workspace=workspace_slug, total=total, items=items)
    except Exception as exc:  # noqa: BLE001
        return _degraded_payload(workspace_slug, exc)
