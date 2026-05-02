from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from loguru import logger

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.user_repo import UserRepository

router = APIRouter(tags=["export"])
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


@router.get("/workspaces/{slug}/export.csv")
async def export_workspace_csv(slug: str, user_id: CurrentUserId) -> Response:
    user_repo = UserRepository()
    if not user_repo.user_owns_workspace(user_id, slug):
        logger.warning("export.forbidden user={} slug={}", user_id, slug)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not accessible")

    prisma = await get_prisma()
    scan_jobs = await prisma.scanjob.find_many(where={"workspaceSlug": slug})
    job_ids = [j.id for j in scan_jobs]

    rows: list[dict[str, str]] = []
    if job_ids:
        executions = await prisma.scanexecution.find_many(where={"scanJobId": {"in": job_ids}})
        exec_by_id = {e.id: e for e in executions}
        prompt_execs = await prisma.promptexecution.find_many(
            where={"scanExecutionId": {"in": list(exec_by_id.keys())}},
        )
        pe_by_id = {pe.id: pe for pe in prompt_execs}
        observations = await prisma.observation.find_many(
            where={"promptExecutionId": {"in": list(pe_by_id.keys())}},
        )
        obs_by_pe_id: dict[str, object] = {o.promptExecutionId: o for o in observations}

        for pe in prompt_execs:
            exec_row = exec_by_id.get(pe.scanExecutionId)
            obs = obs_by_pe_id.get(pe.id)
            executed = getattr(pe, "executedAt", None)
            rows.append(
                {
                    "executed_at": executed.isoformat() if executed is not None else "",
                    "provider": str(getattr(exec_row, "provider", "") or "") if exec_row else "",
                    "prompt": str(getattr(pe, "promptText", "") or ""),
                    "response": str(getattr(pe, "rawResponse", "") or ""),
                    "brand_mentioned": str(bool(getattr(obs, "brandMentioned", False))) if obs else "",
                    "brand_position": (str(getattr(obs, "brandPosition", "") or "") if obs is not None else ""),
                }
            )

    buffer = io.StringIO()
    fieldnames = ["executed_at", "provider", "prompt", "response", "brand_mentioned", "brand_position"]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"citetrack-{slug}-{stamp}.csv"
    logger.info("export.done user={} slug={} rows={}", user_id, slug, len(rows))
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
