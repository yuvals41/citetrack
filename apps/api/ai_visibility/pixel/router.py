from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.pixel.events import PixelEvent
from ai_visibility.pixel.events import VALID_EVENT_TYPES
from ai_visibility.pixel.events import VALID_PIXEL_SOURCES
from ai_visibility.pixel.events import get_pixel_stats
from ai_visibility.pixel.events import store_pixel_event
from ai_visibility.pixel.snippet import generate_pixel_snippet
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pixel", tags=["pixel"])


async def _require_pixel_ownership(user_id: str, workspace_id: str) -> None:
    prisma = cast(object, await get_prisma())
    row = await cast(Any, prisma).workspace.find_unique(where={"id": workspace_id})
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    slug = getattr(row, "slug", None)
    if slug is None or not UserRepository().user_owns_workspace(user_id, slug):
        logger.warning("pixel.forbidden user=%s workspace_id=%s", user_id, workspace_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not accessible")


@router.post("/event")
async def receive_pixel_event(request: Request) -> Response:
    payload: dict[str, Any] = {}
    try:
        body = await request.json()
        payload = body if isinstance(body, dict) else {}
    except Exception:
        logger.warning("[pixel] Invalid JSON body on /event")
    try:
        event = _parse_pixel_event_payload(payload)
        asyncio.create_task(store_pixel_event(event))
    except Exception as exc:
        logger.warning("[pixel] Ignored invalid event: %s", exc)
    return Response(status_code=204, headers={"Access-Control-Allow-Origin": "*"})


@router.get("/snippet/{workspace_id}")
async def get_snippet(workspace_id: str, request: Request, user_id: str = Depends(get_current_user_id)) -> Response:
    await _require_pixel_ownership(user_id, workspace_id)
    api_base_url = f"{request.url.scheme}://{request.url.netloc}"
    snippet = generate_pixel_snippet(workspace_id=workspace_id, api_base_url=api_base_url)
    return Response(content=snippet, media_type="application/javascript")


@router.get("/stats/{workspace_id}")
async def get_stats(workspace_id: str, days: int = 30, user_id: str = Depends(get_current_user_id)) -> dict[str, Any]:
    await _require_pixel_ownership(user_id, workspace_id)
    return await get_pixel_stats(workspace_id=workspace_id, days=days)


def _parse_pixel_event_payload(payload: dict[str, Any]) -> PixelEvent:
    required_fields = ["workspace_id", "source", "referrer", "page_url", "timestamp", "session_id", "event_type"]
    missing_fields = [field for field in required_fields if not payload.get(field)]
    if missing_fields:
        msg = f"missing fields: {', '.join(missing_fields)}"
        raise ValueError(msg)

    source = str(payload["source"]).strip().lower()
    if source not in VALID_PIXEL_SOURCES:
        msg = f"unsupported source: {source}"
        raise ValueError(msg)

    event_type = str(payload["event_type"]).strip().lower()
    if event_type not in VALID_EVENT_TYPES:
        msg = f"unsupported event_type: {event_type}"
        raise ValueError(msg)

    conversion_value = payload.get("conversion_value")
    conversion_currency = payload.get("conversion_currency")

    parsed_conversion_value: float | None = None
    if conversion_value is not None:
        try:
            parsed_conversion_value = float(conversion_value)
        except (TypeError, ValueError) as exc:
            msg = "conversion_value must be numeric"
            raise ValueError(msg) from exc

    parsed_conversion_currency: str | None = None
    if conversion_currency is not None and str(conversion_currency).strip():
        parsed_conversion_currency = str(conversion_currency).strip().upper()

    return PixelEvent(
        workspace_id=str(payload["workspace_id"]),
        source=source,
        referrer=str(payload["referrer"]),
        page_url=str(payload["page_url"]),
        timestamp=str(payload["timestamp"]),
        session_id=str(payload["session_id"]),
        event_type=event_type,
        conversion_value=parsed_conversion_value,
        conversion_currency=parsed_conversion_currency,
    )
