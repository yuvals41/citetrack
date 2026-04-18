from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false

from datetime import datetime
import sqlite3
from typing import Any

from ai_visibility.storage.types import (
    ObservationRecord,
    PromptExecutionCitationRecord,
    PromptExecutionRecord,
    ScanExecutionRecord,
    ScanJobRecord,
)

Prisma = Any


class ScanEvidenceRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def create_scan_job(self, scan_job: ScanJobRecord, *, conn: sqlite3.Connection | None = None) -> bool:
        _ = conn
        existing = await self.prisma.aivisscanjob.find_unique(where={"idempotencyKey": scan_job["idempotency_key"]})
        if existing is not None:
            return False

        await self.prisma.aivisscanjob.upsert(
            where={"idempotencyKey": scan_job["idempotency_key"]},
            data={
                "create": {
                    "id": scan_job["id"],
                    "workspaceSlug": scan_job["workspace_slug"],
                    "strategyVersion": scan_job["strategy_version"],
                    "promptVersion": scan_job["prompt_version"],
                    "createdAt": _parse_datetime(scan_job["created_at"]),
                    "idempotencyKey": scan_job["idempotency_key"],
                    "status": _to_prisma_enum(scan_job["status"]),
                    "scanMode": _to_prisma_enum(scan_job["scan_mode"]),
                },
                "update": {},
            },
        )
        return True

    async def create_scan_execution(
        self,
        scan_execution: ScanExecutionRecord,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> bool:
        _ = conn
        existing = await self.prisma.aivisscanexecution.find_unique(
            where={"idempotencyKey": scan_execution["idempotency_key"]}
        )
        if existing is not None:
            return False

        await self.prisma.aivisscanexecution.upsert(
            where={"idempotencyKey": scan_execution["idempotency_key"]},
            data={
                "create": {
                    "id": scan_execution["id"],
                    "scanJobId": scan_execution["scan_job_id"],
                    "provider": scan_execution["provider"],
                    "modelName": scan_execution["model_name"],
                    "modelVersion": scan_execution["model_version"],
                    "executedAt": _parse_datetime(scan_execution["executed_at"]),
                    "idempotencyKey": scan_execution["idempotency_key"],
                    "status": scan_execution["status"],
                },
                "update": {},
            },
        )
        return True

    async def create_prompt_execution(
        self,
        prompt_execution: PromptExecutionRecord,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> bool:
        _ = conn
        existing = await self.prisma.aivispromptexecution.find_unique(
            where={"idempotencyKey": prompt_execution["idempotency_key"]}
        )
        if existing is not None:
            return False

        await self.prisma.aivispromptexecution.upsert(
            where={"idempotencyKey": prompt_execution["idempotency_key"]},
            data={
                "create": {
                    "id": prompt_execution["id"],
                    "scanExecutionId": prompt_execution["scan_execution_id"],
                    "promptId": prompt_execution["prompt_id"],
                    "promptText": prompt_execution["prompt_text"],
                    "rawResponse": prompt_execution["raw_response"],
                    "executedAt": _parse_datetime(prompt_execution["executed_at"]),
                    "idempotencyKey": prompt_execution["idempotency_key"],
                    "parserVersion": prompt_execution["parser_version"],
                },
                "update": {},
            },
        )
        return True

    async def create_observation(
        self, observation: ObservationRecord, *, conn: sqlite3.Connection | None = None
    ) -> bool:
        _ = conn
        existing = await self.prisma.aivisobservation.find_unique(
            where={"idempotencyKey": observation["idempotency_key"]}
        )
        if existing is not None:
            return False

        await self.prisma.aivisobservation.upsert(
            where={"idempotencyKey": observation["idempotency_key"]},
            data={
                "create": {
                    "id": observation["id"],
                    "promptExecutionId": observation["prompt_execution_id"],
                    "brandMentioned": bool(observation["brand_mentioned"]),
                    "brandPosition": observation["brand_position"],
                    "responseExcerpt": observation["response_excerpt"],
                    "idempotencyKey": observation["idempotency_key"],
                    "strategyVersion": observation["strategy_version"],
                },
                "update": {},
            },
        )
        return True

    async def create_prompt_execution_citation(
        self,
        citation: PromptExecutionCitationRecord,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> bool:
        _ = conn
        existing = await self.prisma.aivispromptexecutioncitation.find_unique(
            where={"idempotencyKey": citation["idempotency_key"]}
        )
        if existing is not None:
            return False

        await self.prisma.aivispromptexecutioncitation.upsert(
            where={"idempotencyKey": citation["idempotency_key"]},
            data={
                "create": {
                    "id": citation["id"],
                    "promptExecutionId": citation["prompt_execution_id"],
                    "url": citation["url"],
                    "title": citation["title"],
                    "citedText": citation["cited_text"],
                    "idempotencyKey": citation["idempotency_key"],
                },
                "update": {},
            },
        )
        return True

    async def list_prompt_executions(self, scan_execution_id: str) -> list[PromptExecutionRecord]:
        rows = await self.prisma.aivispromptexecution.find_many(
            where={"scanExecutionId": scan_execution_id},
            order=[{"executedAt": "asc"}, {"id": "asc"}],
        )
        return [_prompt_execution_from_model(row) for row in rows]

    async def list_observations(self, prompt_execution_id: str) -> list[ObservationRecord]:
        rows = await self.prisma.aivisobservation.find_many(
            where={"promptExecutionId": prompt_execution_id},
            order={"id": "asc"},
        )
        return [_observation_from_model(row) for row in rows]

    async def list_prompt_execution_citations(self, prompt_execution_id: str) -> list[PromptExecutionCitationRecord]:
        rows = await self.prisma.aivispromptexecutioncitation.find_many(
            where={"promptExecutionId": prompt_execution_id},
            order={"id": "asc"},
        )
        return [_citation_from_model(row) for row in rows]


def _prompt_execution_from_model(row: Any) -> PromptExecutionRecord:
    return {
        "id": str(row.id),
        "scan_execution_id": str(row.scanExecutionId),
        "prompt_id": str(row.promptId),
        "prompt_text": str(row.promptText),
        "raw_response": str(row.rawResponse),
        "executed_at": _to_iso(row.executedAt),
        "idempotency_key": str(row.idempotencyKey),
        "parser_version": str(row.parserVersion),
    }


def _observation_from_model(row: Any) -> ObservationRecord:
    return {
        "id": str(row.id),
        "prompt_execution_id": str(row.promptExecutionId),
        "brand_mentioned": bool(row.brandMentioned),
        "brand_position": int(row.brandPosition) if row.brandPosition is not None else None,
        "response_excerpt": str(row.responseExcerpt),
        "idempotency_key": str(row.idempotencyKey),
        "strategy_version": str(row.strategyVersion),
    }


def _citation_from_model(row: Any) -> PromptExecutionCitationRecord:
    return {
        "id": str(row.id),
        "prompt_execution_id": str(row.promptExecutionId),
        "url": str(row.url),
        "title": str(row.title),
        "cited_text": str(row.citedText) if row.citedText is not None else None,
        "idempotency_key": str(row.idempotencyKey),
    }


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _to_iso(value: datetime) -> str:
    return value.isoformat()


def _to_prisma_enum(value: str) -> str:
    return value.upper()
