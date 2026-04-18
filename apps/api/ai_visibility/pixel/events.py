from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from ai_visibility.storage.prisma_connection import get_prisma

logger = logging.getLogger(__name__)

VALID_PIXEL_SOURCES = {"chatgpt", "perplexity", "claude", "gemini", "grok", "copilot", "ai_utm"}
VALID_EVENT_TYPES = {"visit", "conversion"}


@dataclass
class PixelEvent:
    workspace_id: str
    source: str
    referrer: str
    page_url: str
    timestamp: str
    session_id: str
    event_type: str
    conversion_value: float | None = None
    conversion_currency: str | None = None


async def _ensure_pixel_table() -> None:
    prisma = await get_prisma()
    _ = await prisma.execute_raw(
        "CREATE TABLE IF NOT EXISTS ai_vis_pixel_events ("
        "id TEXT PRIMARY KEY, "
        "workspace_id TEXT NOT NULL, "
        "source TEXT NOT NULL, "
        "referrer TEXT, "
        "page_url TEXT, "
        "session_id TEXT, "
        "event_type TEXT NOT NULL DEFAULT 'visit', "
        "conversion_value REAL, "
        "conversion_currency TEXT, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    _ = await prisma.execute_raw(
        "CREATE INDEX IF NOT EXISTS idx_ai_vis_pixel_events_workspace_created "
        "ON ai_vis_pixel_events (workspace_id, created_at)"
    )


async def store_pixel_event(event: PixelEvent) -> None:
    if event.source not in VALID_PIXEL_SOURCES:
        msg = f"[pixel] Unsupported source: {event.source}"
        raise ValueError(msg)
    if event.event_type not in VALID_EVENT_TYPES:
        msg = f"[pixel] Unsupported event type: {event.event_type}"
        raise ValueError(msg)

    await _ensure_pixel_table()
    prisma = await get_prisma()
    _ = await prisma.execute_raw(
        "INSERT INTO ai_vis_pixel_events "
        "(id, workspace_id, source, referrer, page_url, session_id, event_type, conversion_value, conversion_currency, created_at) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, COALESCE($10::timestamp, CURRENT_TIMESTAMP))",
        str(uuid.uuid4()),
        event.workspace_id,
        event.source,
        event.referrer,
        event.page_url,
        event.session_id,
        event.event_type,
        event.conversion_value,
        event.conversion_currency,
        event.timestamp,
    )
    logger.debug(
        "[pixel] Stored event workspace=%s type=%s source=%s", event.workspace_id, event.event_type, event.source
    )


async def get_pixel_stats(workspace_id: str, days: int = 30) -> dict[str, Any]:
    safe_days = max(1, days)
    await _ensure_pixel_table()
    prisma = await get_prisma()

    totals_rows = await prisma.query_raw(
        "SELECT "
        "COUNT(*) FILTER (WHERE event_type = 'visit') AS total_visits, "
        "COUNT(*) FILTER (WHERE event_type = 'conversion') AS total_conversions, "
        "COALESCE(SUM(CASE WHEN event_type = 'conversion' THEN conversion_value ELSE 0 END), 0) AS total_revenue "
        "FROM ai_vis_pixel_events "
        "WHERE workspace_id = $1 AND created_at >= NOW() - make_interval(days => $2::int)",
        workspace_id,
        safe_days,
    )
    source_visit_rows = await prisma.query_raw(
        "SELECT source, COUNT(*) AS count "
        "FROM ai_vis_pixel_events "
        "WHERE workspace_id = $1 AND event_type = 'visit' "
        "AND created_at >= NOW() - make_interval(days => $2::int) "
        "GROUP BY source",
        workspace_id,
        safe_days,
    )
    source_conversion_rows = await prisma.query_raw(
        "SELECT source, COUNT(*) AS count "
        "FROM ai_vis_pixel_events "
        "WHERE workspace_id = $1 AND event_type = 'conversion' "
        "AND created_at >= NOW() - make_interval(days => $2::int) "
        "GROUP BY source",
        workspace_id,
        safe_days,
    )
    daily_rows = await prisma.query_raw(
        "SELECT DATE(created_at) AS date, source, COUNT(*) AS count "
        "FROM ai_vis_pixel_events "
        "WHERE workspace_id = $1 AND event_type = 'visit' "
        "AND created_at >= NOW() - make_interval(days => $2::int) "
        "GROUP BY DATE(created_at), source "
        "ORDER BY DATE(created_at) ASC, source ASC",
        workspace_id,
        safe_days,
    )

    totals = totals_rows[0] if isinstance(totals_rows, list) and totals_rows else {}

    return {
        "total_visits": int(_num(totals.get("total_visits"))),
        "total_conversions": int(_num(totals.get("total_conversions"))),
        "total_revenue": float(_num(totals.get("total_revenue"))),
        "visits_by_source": _source_map(source_visit_rows),
        "conversions_by_source": _source_map(source_conversion_rows),
        "daily_visits": _daily_visits(daily_rows),
    }


def _num(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _source_map(rows: object) -> dict[str, int]:
    result: dict[str, int] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or "")
        if not source:
            continue
        result[source] = int(_num(row.get("count")))
    return result


def _daily_visits(rows: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or "")
        if not source:
            continue
        result.append(
            {
                "date": str(row.get("date") or ""),
                "source": source,
                "count": int(_num(row.get("count"))),
            }
        )
    return result
