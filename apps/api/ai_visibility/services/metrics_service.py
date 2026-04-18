from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from loguru import logger

from ai_visibility.prompts.default_set import DEFAULT_PROMPTS
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository


def _compute_next_scan_display(latest_created_at: object, schedule: str) -> str:
    if schedule == "off":
        return "Off"
    interval_hours = 24 * 7 if schedule == "weekly" else 24
    if latest_created_at is None:
        return "Pending first scheduled run"

    try:
        last_scan = datetime.fromisoformat(str(latest_created_at).replace("Z", "+00:00"))
    except ValueError:
        return ""

    if last_scan.tzinfo is None:
        last_scan = last_scan.replace(tzinfo=timezone.utc)
    next_scan = last_scan.astimezone(timezone.utc) + timedelta(hours=interval_hours)
    return next_scan.strftime("%Y-%m-%d %H:%M UTC")


def _format_timestamp(raw: object) -> str:
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M")
    except (TypeError, ValueError):
        return str(raw) if raw else ""


def _to_float(record: object, key: str) -> float:
    value: object = 0
    if isinstance(record, dict):
        value = record.get(key, 0)
    else:
        value = getattr(record, key, 0)
    if not isinstance(value, (int, float, str)):
        return 0.0
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _to_int(record: object, key: str) -> int:
    value: object = 0
    if isinstance(record, dict):
        value = record.get(key, 0)
    else:
        value = getattr(record, key, 0)
    if not isinstance(value, (int, float, str)):
        return 0
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


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


async def compute_dashboard_metrics(workspace_slug: str) -> dict[str, object]:
    """Compute all dashboard metrics from DB. Returns dict with all metric values."""
    defaults: dict[str, object] = {
        "workspace_found": False,
        "recent_runs": [],
        "next_scan_time": "",
        "provider_breakdown": [],
        "mention_type_breakdown": [],
        "source_breakdown": [],
        "avg_position": 0.0,
        "position_by_provider": [],
        "mentions": [],
        "type_counts": {"explicit": 0, "citation": 0, "absent": 0},
        "visibility_score": 0.0,
        "citation_coverage": 0.0,
        "competitor_wins": 0,
        "has_metrics": False,
        "trend_delta": 0.0,
        "previous_visibility": 0.0,
        "previous_citation_coverage": 0.0,
        "visibility_trend": [],
        "rendered_prompts": [],
    }

    try:
        prisma = await get_prisma()
        ws_repo = WorkspaceRepository(prisma)
        ws = await ws_repo.get_by_slug(workspace_slug)
        if ws is None:
            return defaults

        workspace_id = ws["id"]
        run_repo = RunRepository(prisma)
        runs = await run_repo.list_by_workspace(workspace_id)

        seen_providers: set[str] = set()
        recent_runs: list[dict[str, object]] = []
        for run in runs:
            provider = str(run["provider"])
            if provider in seen_providers:
                continue
            seen_providers.add(provider)
            recent_runs.append(
                {
                    "run_id": run["id"],
                    "status": str(run["status"]).lower().replace("_", " "),
                    "created_at": _format_timestamp(run["created_at"]),
                    "provider": provider,
                    "model": run["model"],
                }
            )

        schedule = str(ws.get("scan_schedule") or "daily")
        latest_created_at = runs[0].get("created_at") if runs else None
        next_scan_time = _compute_next_scan_display(latest_created_at, schedule)

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
            SELECT le.provider, pe.prompt_text, pe.raw_response
            FROM ai_vis_prompt_executions pe
            JOIN latest_executions le ON le.id = pe.scan_execution_id
            ORDER BY le.provider, pe.executed_at ASC, pe.id ASC
            """,
            workspace_slug,
        )

        provider_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {"explicit": 0, "citation": 0, "absent": 0}
        source_counts: dict[str, int] = {}
        provider_positions: dict[str, list[int]] = {}
        mentions: list[dict[str, object]] = []

        brand_slug = workspace_slug.lower()
        brand_name = str(ws.get("brand_name") or workspace_slug)
        candidate_terms = _build_candidate_terms(workspace_slug, brand_name)

        if isinstance(latest_prompt_rows, list):
            for row in latest_prompt_rows:
                if not isinstance(row, dict):
                    continue

                provider = str(row.get("provider") or "unknown")
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

                raw_response = str(row.get("raw_response") or "")
                response_lower = raw_response.lower()
                is_explicit = any(term in response_lower for term in candidate_terms)

                all_urls = re.findall(r"https?://[^\s\)\]\}>,\"']+", raw_response)
                for url in all_urls:
                    try:
                        domain = urlparse(url).netloc.lower()
                    except Exception:  # noqa: BLE001
                        domain = ""
                    if domain.startswith("www."):
                        domain = domain[4:]
                    if domain:
                        source_counts[domain] = source_counts.get(domain, 0) + 1

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

                if is_explicit or brand_cited:
                    mentions.append(
                        {
                            "provider": provider,
                            "raw_response": raw_response,
                            "prompt_text": str(row.get("prompt_text") or ""),
                        }
                    )

                    earliest_pos = len(response_lower)
                    for term in candidate_terms:
                        idx = response_lower.find(term)
                        if idx >= 0 and idx < earliest_pos:
                            earliest_pos = idx

                    if earliest_pos < len(response_lower):
                        ratio = earliest_pos / max(len(response_lower), 1)
                        pos = (
                            1 if ratio < 0.1 else 2 if ratio < 0.25 else 3 if ratio < 0.5 else 4 if ratio < 0.75 else 5
                        )
                        provider_positions.setdefault(provider, []).append(pos)

        provider_breakdown = [
            {"provider": provider, "responses": str(count)} for provider, count in provider_counts.items()
        ]

        mention_colors = {"explicit": "#16a34a", "citation": "#6366f1", "absent": "#ef4444"}
        mention_type_breakdown = [
            {"name": key, "value": value, "fill": mention_colors.get(key, "#6b7280")}
            for key, value in type_counts.items()
        ]

        sorted_sources = sorted(source_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        source_breakdown = [{"domain": domain, "count": str(count)} for domain, count in sorted_sources]

        all_positions = [position for positions in provider_positions.values() for position in positions]
        avg_position = round(sum(all_positions) / len(all_positions), 1) if all_positions else 0.0
        position_by_provider = [
            {"provider": provider, "position": str(round(sum(positions) / len(positions), 1))}
            for provider, positions in provider_positions.items()
        ]

        total_responses = sum(type_counts.values())
        mentioned_count = type_counts.get("explicit", 0) + type_counts.get("citation", 0)
        citation_count = type_counts.get("citation", 0)
        computed_visibility = mentioned_count / total_responses if total_responses > 0 else 0.0
        computed_citation_coverage = citation_count / total_responses if total_responses > 0 else 0.0

        metric_repo = MetricRepository(prisma)
        snapshot = await metric_repo.get_latest_by_workspace(workspace_id)
        previous_snapshot = await metric_repo.get_previous_by_workspace(workspace_id) if snapshot is not None else None

        has_metrics = snapshot is not None
        competitor_wins = _to_int(snapshot, "competitor_wins") if snapshot is not None else 0
        trend_delta = (
            round(_to_float(snapshot, "visibility_score") - _to_float(previous_snapshot, "visibility_score"), 4)
            if snapshot is not None and previous_snapshot is not None
            else 0.0
        )
        previous_visibility = _to_float(previous_snapshot, "visibility_score") if previous_snapshot is not None else 0.0
        previous_citation_coverage = (
            _to_float(previous_snapshot, "citation_coverage") if previous_snapshot is not None else 0.0
        )

        visibility_trend: list[dict[str, str]] = []
        try:
            snapshots = await metric_repo.list_by_workspace(workspace_id)
            visibility_trend = [
                {
                    "scan": str(index + 1),
                    "score": str(round(float(snapshot_row["visibility_score"]) * 100, 1)),
                }
                for index, snapshot_row in enumerate(snapshots)
            ]
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"[metrics_service] trend computation failed: {type(exc).__name__}: {exc}")

        brand_display = workspace_slug.replace("-", " ").title()
        custom_prompts_rows = await prisma.query_raw(
            'SELECT "text" FROM "ai_vis_prompts" WHERE "workspace_id" = $1 ORDER BY "created_at" ASC',
            workspace_id,
        )
        custom_prompts = [
            {"category": "custom", "question": str(row.get("text", "")).strip()}
            for row in custom_prompts_rows
            if isinstance(row, dict) and str(row.get("text", "")).strip()
        ]
        rendered_prompts = [
            {
                "category": prompt.get("category", "general"),
                "question": str(prompt["template"])
                .replace("{brand}", brand_display)
                .replace("{competitor}", "competitors"),
            }
            for prompt in DEFAULT_PROMPTS
        ]
        rendered_prompts.extend(custom_prompts)

        return {
            "workspace_found": True,
            "workspace_id": workspace_id,
            "recent_runs": recent_runs,
            "next_scan_time": next_scan_time,
            "provider_breakdown": provider_breakdown,
            "mention_type_breakdown": mention_type_breakdown,
            "source_breakdown": source_breakdown,
            "avg_position": avg_position,
            "position_by_provider": position_by_provider,
            "mentions": mentions,
            "type_counts": type_counts,
            "visibility_score": round(computed_visibility * 100) / 100,
            "citation_coverage": round(computed_citation_coverage * 100) / 100,
            "competitor_wins": competitor_wins,
            "has_metrics": has_metrics,
            "trend_delta": trend_delta,
            "previous_visibility": previous_visibility,
            "previous_citation_coverage": previous_citation_coverage,
            "visibility_trend": visibility_trend,
            "rendered_prompts": rendered_prompts,
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"[metrics_service] failed for {workspace_slug}: {type(exc).__name__}: {exc}")
        return defaults
