from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false

import sqlite3
from typing import Any, Literal

from ai_visibility.storage.types import CitationRecord, MentionRecord

Prisma = Any


class MentionRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def create_bulk(self, mentions: list[MentionRecord], *, conn: sqlite3.Connection | None = None) -> None:
        if not mentions:
            return

        _ = conn
        for mention in mentions:
            await self.prisma.aivismention.create(
                data={
                    "id": mention["id"],
                    "workspaceId": mention["workspace_id"],
                    "runId": mention["run_id"],
                    "brandId": mention["brand_id"],
                    "mentionType": mention["mention_type"],
                    "text": mention["text"],
                    "citationUrl": mention["citation"].get("url"),
                    "citationDomain": mention["citation"].get("domain"),
                    "citationStatus": _to_prisma_enum(mention["citation"]["status"]),
                }
            )

    async def list_by_run(self, run_id: str) -> list[MentionRecord]:
        rows = await self.prisma.aivismention.find_many(
            where={"runId": run_id},
            order={"id": "asc"},
        )

        return [_mention_from_model(row) for row in rows]


def _mention_from_model(row: Any) -> MentionRecord:
    citation_status = _from_prisma_enum(row.citationStatus)
    url = row.citationUrl
    domain = row.citationDomain
    status: Literal["found", "no_citation"]
    if citation_status == "found":
        status = "found"
    else:
        status = "no_citation"

    citation: CitationRecord = {
        "url": None if url is None else str(url),
        "domain": None if domain is None else str(domain),
        "status": status,
    }

    mention: MentionRecord = {
        "id": str(row.id),
        "workspace_id": str(row.workspaceId),
        "run_id": str(row.runId),
        "brand_id": str(row.brandId),
        "mention_type": str(row.mentionType),
        "text": str(row.text),
        "citation": citation,
    }

    return mention


def _to_prisma_enum(value: str) -> str:
    return value.upper()


def _from_prisma_enum(value: Any) -> str:
    raw = str(value)
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    return raw.lower()
