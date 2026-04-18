from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

cron: Any = getattr(import_module("arq"), "cron")
RedisSettings: Any = getattr(import_module("arq.connections"), "RedisSettings")

logger = logging.getLogger(__name__)

SCAN_PROVIDERS = ["openai", "anthropic", "gemini", "perplexity", "grok", "google_ai_overview"]
SCHEDULE_HOURS = {
    "daily": 24,
    "weekly": 24 * 7,
}


def _to_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


async def _build_competitor_scores(
    prisma: Any,
    workspace_id: str,
    workspace_slug: str,
    brand_visibility: float,
) -> list[dict[str, object]]:
    prompt_rows = await prisma.query_raw(
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
        ORDER BY pe.executed_at ASC, pe.id ASC
        """,
        workspace_slug,
    )

    responses = [str(row.get("raw_response") or "").lower() for row in prompt_rows if isinstance(row, dict)]
    total_responses = len(responses)

    competitor_scores: list[dict[str, object]] = [
        {"name": workspace_slug, "score": f"{brand_visibility:.2f}", "is_brand": "true"}
    ]

    competitors = await prisma.query_raw(
        'SELECT "name" FROM "ai_vis_competitors" WHERE "workspace_id" = $1',
        workspace_id,
    )
    if not isinstance(competitors, list):
        return competitor_scores

    for competitor in competitors:
        if not isinstance(competitor, dict):
            continue
        raw_name = str(competitor.get("name") or "").strip()
        if not raw_name:
            continue
        competitor_name = raw_name.split("(")[0].strip()
        if not competitor_name:
            continue
        competitor_lower = competitor_name.lower()
        mention_count = sum(1 for text in responses if competitor_lower in text)
        visibility = round(mention_count / total_responses, 2) if total_responses > 0 else 0.0
        competitor_scores.append(
            {
                "name": competitor_name,
                "score": f"{visibility:.2f}",
                "is_brand": "false",
            }
        )

    return competitor_scores


async def run_scheduled_scans(ctx: dict[str, object]) -> None:
    _ = ctx
    logger.info("Starting scheduled scan check")

    try:
        prisma = await get_prisma()
        alerts_engine = import_module("ai_visibility.alerts.engine")
        alerts_webhook = import_module("ai_visibility.alerts.webhook")
        alerts_email = import_module("ai_visibility.alerts.email_alert")
        detect_alerts_fn = getattr(alerts_engine, "detect_alerts")
        send_webhook_fn = getattr(alerts_webhook, "send_webhook")
        send_email_alert_fn = getattr(alerts_email, "send_email_alert")
        ws_repo = WorkspaceRepository(prisma)
        run_repo = RunRepository(prisma)
        workspaces = await ws_repo.list_all()
        if not workspaces:
            logger.info("No workspaces found")
            return

        now = datetime.now(timezone.utc)
        metric_repo = MetricRepository(prisma)

        for ws in workspaces:
            workspace_id = ws["id"]
            slug = ws["slug"]
            schedule = str(ws.get("scan_schedule") or "daily")
            if schedule == "off":
                logger.info("Workspace %s: schedule is off, skipping", slug)
                continue

            interval_hours = SCHEDULE_HOURS.get(schedule, 24)
            latest_run = await run_repo.get_latest_by_workspace(workspace_id)
            if latest_run is not None:
                last_scan = _to_datetime(latest_run.get("created_at"))
                if last_scan is not None:
                    hours_since = (now - last_scan).total_seconds() / 3600
                    if hours_since < interval_hours:
                        logger.info(
                            "Workspace %s: scanned %.1fh ago (< %sh), skipping",
                            slug,
                            hours_since,
                            interval_hours,
                        )
                        continue

            logger.info("Workspace %s: running scheduled scan (%s)", slug, schedule)
            pre_scan_snapshot = await metric_repo.get_latest_by_workspace(workspace_id)
            for provider in SCAN_PROVIDERS:
                try:
                    orchestrator = RunOrchestrator(workspace_slug=slug, provider=provider)
                    result = await orchestrator.scan(dry_run=False)
                    logger.info("Workspace %s %s: %s", slug, provider, result.status)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Workspace %s %s failed: %s", slug, provider, exc)

            current_snapshot = await metric_repo.get_latest_by_workspace(workspace_id)
            prev_vis = float(pre_scan_snapshot["visibility_score"]) if pre_scan_snapshot else 0.0
            prev_cit = float(pre_scan_snapshot["citation_coverage"]) if pre_scan_snapshot else 0.0
            current_vis = float(current_snapshot["visibility_score"]) if current_snapshot else 0.0
            current_cit = float(current_snapshot["citation_coverage"]) if current_snapshot else 0.0
            comp_scores = await _build_competitor_scores(prisma, workspace_id, slug, current_vis)
            alerts = detect_alerts_fn(
                current_visibility=current_vis,
                previous_visibility=prev_vis,
                current_citation_coverage=current_cit,
                previous_citation_coverage=prev_cit,
                competitor_scores=comp_scores,
                brand_slug=slug,
            )
            if alerts:
                await send_webhook_fn(alerts, slug)
                await send_email_alert_fn(alerts, slug)

        logger.info("Scheduled scan check complete")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scheduled scan failed: %s", exc)
    finally:
        try:
            await disconnect_prisma()
        except Exception as e:  # noqa: BLE001
            logger.debug(f"[worker] Failed to disconnect Prisma: {type(e).__name__}: {e}")


def compute_next_scan_display(latest_created_at: object, schedule: str) -> str:
    if schedule == "off":
        return "Off"
    hours = SCHEDULE_HOURS.get(schedule, 24)
    latest = _to_datetime(latest_created_at)
    if latest is None:
        return "Pending first scheduled run"
    next_scan = latest + timedelta(hours=hours)
    return next_scan.strftime("%Y-%m-%d %H:%M UTC")


class WorkerSettings:
    functions: list[Any] = [run_scheduled_scans]
    cron_jobs: list[Any] = [
        cron(run_scheduled_scans, hour=6, minute=0),
    ]
    redis_settings: Any = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
    max_jobs: int = 1
    job_timeout: int = 1800
