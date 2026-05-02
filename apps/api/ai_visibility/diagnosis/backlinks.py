from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, cast

BACKLINK_GAP = "backlink_gap"
GROUNDED_SEARCH_AUTHORITY_WEAK = "grounded_search_authority_weak"
COMPETITOR_GAP = "competitor_gap"

_MIN_REFERRING_DOMAINS = 30.0
_MIN_DOMAIN_RANK = 40.0
_MIN_GROUNDED_AUTHORITY_DOMAINS = 3.0
_MIN_GROUNDED_CITATIONS = 2.0
_MIN_LOCAL_AUTHORITY_CITATIONS = 3.0
_COMPETITOR_GAP_RATIO = 1.5
_COMPETITOR_GAP_DIFF = 20.0


class FindingEvidence(TypedDict):
    check: str
    value: object
    source: str


class BacklinkFinding(TypedDict):
    reason_code: str
    evidence: list[FindingEvidence]
    confidence: float
    applicability: str


class BacklinkDiagnoser:
    def ingest(self, payload: dict[str, object]) -> list[dict[str, object]]:
        normalized_payload = _unwrap_task_result(cast(object, payload))
        findings: list[BacklinkFinding] = []

        backlink_gap = self._backlink_gap_finding(normalized_payload)
        if backlink_gap is not None:
            findings.append(backlink_gap)

        grounded_authority = self._grounded_search_authority_finding(normalized_payload)
        if grounded_authority is not None:
            findings.append(grounded_authority)

        competitor_gap = self._competitor_gap_finding(normalized_payload)
        if competitor_gap is not None:
            findings.append(competitor_gap)

        return cast(list[dict[str, object]], findings)

    def _backlink_gap_finding(self, payload: Mapping[str, object]) -> BacklinkFinding | None:
        summary = _summary_section(payload)
        has_referring_domains = _has_any_key(summary, "referring_domains", "referring_main_domains")
        has_domain_rank = _has_any_key(summary, "domain_rank", "rank", "domain_from_rank")
        if not has_referring_domains and not has_domain_rank:
            return None

        referring_domains = _first_number(summary, "referring_domains", "referring_main_domains")
        domain_rank = _first_number(summary, "domain_rank", "rank", "domain_from_rank")

        evidence: list[FindingEvidence] = []
        weak_signals = 0
        if has_referring_domains:
            evidence.append(
                {
                    "check": "referring_domains",
                    "value": int(referring_domains),
                    "source": "summary.referring_domains",
                }
            )
            if referring_domains < _MIN_REFERRING_DOMAINS:
                weak_signals += 1

        if has_domain_rank:
            evidence.append(
                {
                    "check": "domain_rank",
                    "value": round(domain_rank, 2),
                    "source": "summary.domain_rank",
                }
            )
            if domain_rank < _MIN_DOMAIN_RANK:
                weak_signals += 1

        if weak_signals == 0:
            return None

        if has_referring_domains:
            evidence.append(
                {
                    "check": "referring_domain_threshold",
                    "value": int(_MIN_REFERRING_DOMAINS),
                    "source": "rule.backlink_gap.referring_domains",
                }
            )
        if has_domain_rank:
            evidence.append(
                {
                    "check": "domain_rank_threshold",
                    "value": int(_MIN_DOMAIN_RANK),
                    "source": "rule.backlink_gap.domain_rank",
                }
            )

        severity_bonus = 0.0
        if has_referring_domains and referring_domains < 10:
            severity_bonus += 0.1
        if has_domain_rank and domain_rank < 20:
            severity_bonus += 0.08

        return {
            "reason_code": BACKLINK_GAP,
            "evidence": evidence,
            "confidence": min(0.92, 0.5 + (weak_signals * 0.14) + severity_bonus),
            "applicability": "all",
        }

    def _grounded_search_authority_finding(self, payload: Mapping[str, object]) -> BacklinkFinding | None:
        authority = _authority_section(payload)
        if not authority:
            return None

        nested_grounded = _section(authority, "grounded_search")
        grounded = nested_grounded if nested_grounded else _grounded_authority_section(authority)
        providers = _grounded_provider_names(grounded if grounded else authority)
        if not grounded and not providers:
            return None

        source_prefix = "authority_signals.grounded_search" if nested_grounded else "authority_signals"
        authority_source = grounded if grounded else authority
        summary = _summary_section(payload)
        has_referring_domains = _has_any_key(summary, "referring_domains", "referring_main_domains")
        referring_domains = _first_number(summary, "referring_domains", "referring_main_domains")
        authoritative_referring_domains = _first_number(
            authority_source,
            "authoritative_referring_domains",
            "trusted_referring_domains",
            "expert_referring_domains",
        )
        authoritative_citations = _first_number(
            authority_source,
            "authoritative_citations",
            "grounded_citations",
            "expert_source_citations",
        )
        local_brand = _local_brand_required(authority)
        local_authority_citations = _first_number(
            authority_source,
            "local_authority_citations",
            "local_citations",
            "map_pack_citations",
        )

        evidence: list[FindingEvidence] = [
            {
                "check": "grounded_search_providers",
                "value": providers,
                "source": f"{source_prefix}.providers",
            },
            {
                "check": "authoritative_referring_domains",
                "value": int(authoritative_referring_domains),
                "source": f"{source_prefix}.authoritative_referring_domains",
            },
            {
                "check": "authoritative_citations",
                "value": int(authoritative_citations),
                "source": f"{source_prefix}.authoritative_citations",
            },
        ]
        if has_referring_domains:
            evidence.append(
                {
                    "check": "referring_domains",
                    "value": int(referring_domains),
                    "source": "summary.referring_domains",
                }
            )
        if local_brand:
            evidence.append(
                {
                    "check": "local_authority_citations",
                    "value": int(local_authority_citations),
                    "source": f"{source_prefix}.local_authority_citations",
                }
            )

        weak_signals = 0
        if authoritative_referring_domains < _MIN_GROUNDED_AUTHORITY_DOMAINS:
            weak_signals += 1
        if authoritative_citations < _MIN_GROUNDED_CITATIONS:
            weak_signals += 1
        if has_referring_domains and referring_domains < _MIN_REFERRING_DOMAINS:
            weak_signals += 1
        if local_brand and local_authority_citations < _MIN_LOCAL_AUTHORITY_CITATIONS:
            weak_signals += 1

        if weak_signals == 0:
            return None

        return {
            "reason_code": GROUNDED_SEARCH_AUTHORITY_WEAK,
            "evidence": evidence,
            "confidence": min(0.9, 0.44 + (weak_signals * 0.13)),
            "applicability": "grounded_search",
        }

    def _competitor_gap_finding(self, payload: Mapping[str, object]) -> BacklinkFinding | None:
        competitor_gap = _competitor_gap_section(payload)
        if not competitor_gap:
            return None

        summary = _summary_section(payload)
        target_referring_domains = _target_referring_domains(competitor_gap)
        if target_referring_domains == 0 and _has_any_key(summary, "referring_domains", "referring_main_domains"):
            target_referring_domains = _first_number(summary, "referring_domains", "referring_main_domains")

        competitors = _competitor_entries(competitor_gap)
        if not competitors:
            return None

        competitor_domains = [
            (domain, referring_domains) for domain, referring_domains in competitors if referring_domains > 0
        ]
        if not competitor_domains:
            return None

        stronger_competitors = [
            domain for domain, referring_domains in competitor_domains if referring_domains > target_referring_domains
        ]
        strongest_competitor_domains = max(referring_domains for _, referring_domains in competitor_domains)
        average_competitor_domains = sum(referring_domains for _, referring_domains in competitor_domains) / len(
            competitor_domains
        )
        ratio = strongest_competitor_domains / max(target_referring_domains, 1.0)
        absolute_gap = strongest_competitor_domains - target_referring_domains

        if not stronger_competitors:
            return None
        if ratio < _COMPETITOR_GAP_RATIO and absolute_gap < _COMPETITOR_GAP_DIFF:
            return None

        evidence: list[FindingEvidence] = [
            {
                "check": "target_referring_domains",
                "value": int(target_referring_domains),
                "source": "competitor_gap.target.referring_domains",
            },
            {
                "check": "average_competitor_referring_domains",
                "value": round(average_competitor_domains, 2),
                "source": "competitor_gap.competitors[].referring_domains",
            },
            {
                "check": "strongest_competitor_referring_domains",
                "value": int(strongest_competitor_domains),
                "source": "competitor_gap.competitors[].referring_domains",
            },
            {
                "check": "stronger_competitor_domains",
                "value": stronger_competitors,
                "source": "competitor_gap.competitors[].domain",
            },
        ]

        return {
            "reason_code": COMPETITOR_GAP,
            "evidence": evidence,
            "confidence": min(0.94, 0.52 + (min(ratio, 3.0) * 0.1)),
            "applicability": "all",
        }


def _summary_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    summary = _section(payload, "summary")
    if summary:
        return summary
    return payload


def _authority_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    authority = _section(payload, "authority_signals")
    if authority:
        return authority
    if _grounded_context_present(payload):
        return payload
    return {}


def _grounded_authority_section(authority: Mapping[str, object]) -> Mapping[str, object]:
    grounded = _section(authority, "grounded_search")
    if grounded:
        return grounded
    if _grounded_context_present(authority):
        return authority
    return {}


def _competitor_gap_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    competitor_gap = _section(payload, "competitor_gap")
    if competitor_gap:
        return competitor_gap
    if _items_for_key(payload, "competitors"):
        return payload
    return {}


def _grounded_context_present(payload: Mapping[str, object]) -> bool:
    if _grounded_provider_names(payload):
        return True
    return _has_any_key(
        payload,
        "authoritative_referring_domains",
        "trusted_referring_domains",
        "expert_referring_domains",
        "authoritative_citations",
        "grounded_citations",
        "expert_source_citations",
    )


def _grounded_provider_names(section: Mapping[str, object]) -> list[str]:
    providers: list[str] = []
    raw_providers = section.get("providers")
    if isinstance(raw_providers, str) and raw_providers.strip():
        providers.append(raw_providers.strip())
    elif isinstance(raw_providers, Sequence) and not isinstance(raw_providers, (str, bytes)):
        for provider in raw_providers:
            if isinstance(provider, str) and provider.strip():
                providers.append(provider.strip())
            elif isinstance(provider, Mapping):
                provider_name = _first_text(cast(Mapping[str, object], provider), "name", "provider")
                mode = _first_text(cast(Mapping[str, object], provider), "mode", "applicability")
                if provider_name and (not mode or mode == "grounded_search"):
                    providers.append(provider_name)

    provider_modes = _mapping(section.get("provider_modes"))
    for raw_provider_name, provider_mode in provider_modes.items():
        if _is_grounded_mode(provider_mode):
            providers.append(str(raw_provider_name))

    unique_providers: list[str] = []
    seen: set[str] = set()
    for provider in providers:
        normalized = provider.strip()
        if normalized and normalized not in seen:
            unique_providers.append(normalized)
            seen.add(normalized)
    return unique_providers


def _is_grounded_mode(mode: object) -> bool:
    if isinstance(mode, str):
        return mode.strip().lower() == "grounded_search"
    if isinstance(mode, Mapping):
        mode_mapping = cast(Mapping[str, object], mode)
        return _is_grounded_mode(mode_mapping.get("mode")) or _as_bool(mode_mapping.get("grounded"))
    return False


def _local_brand_required(section: Mapping[str, object]) -> bool:
    for key in ("is_local_brand", "local_brand", "requires_local_authority"):
        if key in section:
            return _as_bool(section.get(key))
    return False


def _target_referring_domains(section: Mapping[str, object]) -> float:
    target = _section(section, "target")
    if target:
        value = _first_number(target, "referring_domains", "referring_main_domains")
        if value or _has_any_key(target, "referring_domains", "referring_main_domains"):
            return value
    return _first_number(section, "target_referring_domains")


def _competitor_entries(section: Mapping[str, object]) -> list[tuple[str, float]]:
    entries = _items_for_key(section, "competitors")
    if not entries:
        entries = _items(section)

    competitor_entries: list[tuple[str, float]] = []
    for entry in entries:
        domain = _first_text(entry, "domain", "target", "competitor") or "unknown"
        referring_domains = _first_number(entry, "referring_domains", "referring_main_domains")
        competitor_entries.append((domain, referring_domains))
    return competitor_entries


def _section(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    section = payload.get(key)
    if section is None:
        return {}
    return _unwrap_task_result(section)


def _unwrap_task_result(value: object) -> Mapping[str, object]:
    mapping = _mapping(value)
    if not mapping:
        return {}

    tasks = mapping.get("tasks")
    if not isinstance(tasks, Sequence) or isinstance(tasks, (str, bytes)):
        return mapping

    for task in tasks:
        task_mapping = _mapping(task)
        if not task_mapping:
            continue
        status_code = task_mapping.get("status_code")
        if status_code not in (None, 20000, "20000"):
            continue
        result = task_mapping.get("result")
        if isinstance(result, Sequence) and not isinstance(result, (str, bytes)) and result:
            first_result = _mapping(result[0])
            if first_result:
                return first_result
    return {}


def _items(section: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_items = section.get("items")
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        return []
    return [_mapping(item) for item in raw_items if _mapping(item)]


def _items_for_key(section: Mapping[str, object], key: str) -> list[Mapping[str, object]]:
    raw_items = section.get(key)
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        return []
    return [_mapping(item) for item in raw_items if _mapping(item)]


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return {}


def _has_any_key(mapping: Mapping[str, object], *keys: str) -> bool:
    return any(key in mapping for key in keys)


def _first_number(item: Mapping[str, object], *keys: str) -> float:
    for key in keys:
        if key not in item:
            continue
        return _as_number(item.get(key))
    return 0.0


def _first_text(item: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _as_number(value: object) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0
