from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, cast

CANONICAL_REASON_CODES: tuple[str, ...] = (
    "ai_crawler_blocked",
    "ambiguous_brand",
    "backlink_gap",
    "competitor_gap",
    "content_answer_gap",
    "entity_clarity_weak",
    "grounded_search_authority_weak",
    "kg_presence_missing",
    "missing_citations",
    "missing_quotations",
    "missing_statistics",
    "schema_missing",
    "technical_barrier",
)

_VALID_APPLICABILITY = {"all", "grounded_search"}


class FindingEvidence(TypedDict):
    check: str
    value: object
    source: str


class Finding(TypedDict):
    reason_code: str
    evidence: list[FindingEvidence]
    confidence: float
    applicability: str


class FindingsPipeline:
    def generate(self, diagnosis_results: list[dict[str, object]]) -> list[dict[str, object]]:
        if not diagnosis_results:
            return []

        aggregated: dict[str, Finding] = {}
        for finding in diagnosis_results:
            normalized = self._normalize_finding(cast(object, finding))
            if normalized is None:
                continue

            reason_code = normalized["reason_code"]
            existing = aggregated.get(reason_code)
            if existing is None:
                aggregated[reason_code] = normalized
                continue

            existing["confidence"] = max(existing["confidence"], normalized["confidence"])
            existing["applicability"] = self._merge_applicability(
                existing["applicability"],
                normalized["applicability"],
            )
            existing["evidence"] = self._merge_evidence(existing["evidence"], normalized["evidence"])

        ordered_findings = sorted(
            aggregated.values(),
            key=lambda item: (-item["confidence"], item["reason_code"]),
        )
        return cast(list[dict[str, object]], ordered_findings)

    def _normalize_finding(self, raw: object) -> Finding | None:
        if not isinstance(raw, Mapping):
            return None

        mapping = cast(Mapping[str, object], raw)

        reason_code = mapping.get("reason_code")
        if not isinstance(reason_code, str) or not reason_code.strip():
            return None

        confidence = self._as_confidence(mapping.get("confidence"))
        applicability = self._normalize_applicability(mapping.get("applicability"))
        evidence = self._normalize_evidence(mapping.get("evidence"))

        return {
            "reason_code": reason_code.strip(),
            "evidence": evidence,
            "confidence": confidence,
            "applicability": applicability,
        }

    def _normalize_evidence(self, raw: object) -> list[FindingEvidence]:
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            return []

        normalized: list[FindingEvidence] = []
        seen: set[tuple[str, str, str]] = set()
        for entry in raw:
            if not isinstance(entry, Mapping):
                continue

            mapping = cast(Mapping[str, object], entry)

            check = mapping.get("check")
            source = mapping.get("source")
            if not isinstance(check, str) or not check.strip():
                continue
            if not isinstance(source, str) or not source.strip():
                continue

            evidence: FindingEvidence = {
                "check": check.strip(),
                "value": mapping.get("value"),
                "source": source.strip(),
            }
            fingerprint = (evidence["check"], repr(evidence["value"]), evidence["source"])
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            normalized.append(evidence)
        return normalized

    def _merge_evidence(
        self,
        left: list[FindingEvidence],
        right: list[FindingEvidence],
    ) -> list[FindingEvidence]:
        merged: list[FindingEvidence] = []
        seen: set[tuple[str, str, str]] = set()
        for evidence in [*left, *right]:
            fingerprint = (evidence["check"], repr(evidence["value"]), evidence["source"])
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            merged.append(evidence)
        return merged

    def _normalize_applicability(self, raw: object) -> str:
        if not isinstance(raw, str):
            return "all"

        normalized = raw.strip().lower()
        if normalized == "web":
            return "all"
        if normalized in _VALID_APPLICABILITY:
            return normalized
        return "all"

    def _merge_applicability(self, left: str, right: str) -> str:
        if left == right:
            return left
        if "all" in {left, right}:
            return "all"
        return "all"

    def _as_confidence(self, raw: object) -> float:
        if isinstance(raw, bool):
            return 1.0 if raw else 0.0
        if isinstance(raw, (int, float)):
            return max(0.0, min(1.0, float(raw)))
        return 0.0
