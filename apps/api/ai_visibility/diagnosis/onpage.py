from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, cast

SCHEMA_MISSING = "schema_missing"
CONTENT_ANSWER_GAP = "content_answer_gap"
TECHNICAL_BARRIER = "technical_barrier"
AI_CRAWLER_BLOCKED = "ai_crawler_blocked"
MISSING_CITATIONS = "missing_citations"
MISSING_STATISTICS = "missing_statistics"
MISSING_QUOTATIONS = "missing_quotations"

_GENERIC_SCHEMA_TYPES = {"thing", "organization", "webpage", "website"}
_TECHNICAL_CHECKS = {
    "is_4xx_code": "summary.page_metrics.checks.is_4xx_code",
    "is_5xx_code": "summary.page_metrics.checks.is_5xx_code",
    "is_redirect_chain": "summary.page_metrics.checks.is_redirect_chain",
    "is_broken": "summary.page_metrics.checks.is_broken",
}
_AI_CRAWLERS = {
    "gptbot": "GPTBot",
    "oai-searchbot": "OAI-SearchBot",
    "perplexitybot": "PerplexityBot",
    "google-extended": "Google-Extended",
    "claudebot": "ClaudeBot",
    "ccbot": "CCBot",
}


class FindingEvidence(TypedDict):
    check: str
    value: object
    source: str


class OnPageFinding(TypedDict):
    reason_code: str
    evidence: list[FindingEvidence]
    confidence: float
    applicability: str


class OnPageDiagnoser:
    def ingest(self, payload: dict[str, object]) -> list[dict[str, object]]:
        normalized_payload = _unwrap_task_result(cast(object, payload))
        findings: list[OnPageFinding] = []

        schema_finding = self._schema_finding(normalized_payload)
        if schema_finding is not None:
            findings.append(schema_finding)

        content_finding = self._content_finding(normalized_payload)
        if content_finding is not None:
            findings.append(content_finding)

        citation_finding = self._citation_finding(normalized_payload)
        if citation_finding is not None:
            findings.append(citation_finding)

        statistics_finding = self._statistics_finding(normalized_payload)
        if statistics_finding is not None:
            findings.append(statistics_finding)

        quotation_finding = self._quotation_finding(normalized_payload)
        if quotation_finding is not None:
            findings.append(quotation_finding)

        technical_finding = self._technical_finding(normalized_payload)
        if technical_finding is not None:
            findings.append(technical_finding)

        ai_crawler_finding = self._ai_crawler_finding(normalized_payload)
        if ai_crawler_finding is not None:
            findings.append(ai_crawler_finding)

        return cast(list[dict[str, object]], findings)

    def _schema_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        items = _microdata_items(payload)
        if not items:
            return {
                "reason_code": SCHEMA_MISSING,
                "evidence": [
                    {
                        "check": "microdata_items",
                        "value": 0,
                        "source": "microdata.items",
                    },
                    {
                        "check": "rich_schema_types",
                        "value": [],
                        "source": "microdata.items[].types",
                    },
                ],
                "confidence": 0.35,
                "applicability": "web",
            }

        observed_types: set[str] = set()
        rich_types: set[str] = set()
        for item in items:
            types = _schema_types(item)
            observed_types.update(types)
            rich_types.update(schema_type for schema_type in types if schema_type.lower() not in _GENERIC_SCHEMA_TYPES)

        if rich_types:
            return None

        evidence: list[FindingEvidence] = [
            {
                "check": "microdata_items",
                "value": len(items),
                "source": "microdata.items",
            },
            {
                "check": "schema_types",
                "value": sorted(observed_types),
                "source": "microdata.items[].types",
            },
            {
                "check": "rich_schema_types",
                "value": sorted(rich_types),
                "source": "microdata.items[].types",
            },
        ]
        confidence = 0.82 if not observed_types else 0.68
        return {
            "reason_code": SCHEMA_MISSING,
            "evidence": evidence,
            "confidence": confidence,
            "applicability": "web",
        }

    def _content_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        items = _content_items(payload)
        if not items:
            return None

        word_counts = [count for item in items if (count := _content_word_count(item)) > 0]
        faq_sections = sum(_first_number(item, "faq_sections", "faq_count", "questions_answered") for item in items)
        data_tables = sum(_first_number(item, "tables", "table_count", "data_tables") for item in items)
        thin_pages = sum(1 for count in word_counts if count < 120)
        average_words = sum(word_counts) / len(word_counts) if word_counts else 0.0

        if word_counts and average_words >= 120 and faq_sections > 0 and data_tables > 0:
            return None

        evidence: list[FindingEvidence] = [
            {
                "check": "content_items",
                "value": len(items),
                "source": "content_parsing.items",
            },
            {
                "check": "average_word_count",
                "value": round(average_words, 2),
                "source": "content_parsing.items[].plain_text_word_count",
            },
            {
                "check": "thin_pages_below_120_words",
                "value": thin_pages,
                "source": "content_parsing.items[].plain_text_word_count",
            },
            {
                "check": "faq_sections",
                "value": faq_sections,
                "source": "content_parsing.items[].faq_sections",
            },
            {
                "check": "data_tables",
                "value": data_tables,
                "source": "content_parsing.items[].tables",
            },
        ]

        signals = 0
        if not word_counts or average_words < 120:
            signals += 1
        if faq_sections == 0:
            signals += 1
        if data_tables == 0:
            signals += 1

        return {
            "reason_code": CONTENT_ANSWER_GAP,
            "evidence": evidence,
            "confidence": min(0.9, 0.45 + (signals * 0.15)),
            "applicability": "web",
        }

    def _technical_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        evidence: list[FindingEvidence] = []
        checks = _summary_checks(payload)
        for check_name, source in _TECHNICAL_CHECKS.items():
            count = _as_number(checks.get(check_name))
            if count > 0:
                evidence.append({"check": check_name, "value": count, "source": source})

        technical = _section(payload, "technical")
        broken_pages = _items_for_key(technical, "broken_pages")
        if broken_pages:
            evidence.append(
                {
                    "check": "broken_pages",
                    "value": len(broken_pages),
                    "source": "technical.broken_pages",
                }
            )

        redirect_chains = _items_for_key(technical, "redirect_chains")
        if redirect_chains:
            evidence.append(
                {
                    "check": "redirect_chains",
                    "value": len(redirect_chains),
                    "source": "technical.redirect_chains",
                }
            )

        if not evidence:
            return None

        return {
            "reason_code": TECHNICAL_BARRIER,
            "evidence": evidence,
            "confidence": min(0.95, 0.55 + (len(evidence) * 0.08)),
            "applicability": "web",
        }

    def _ai_crawler_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        robots_txt = _robots_txt_content(payload)
        if not robots_txt:
            return None

        blocked_crawlers = sorted(
            user_agent for user_agent in _AI_CRAWLERS.values() if _is_user_agent_disallowed(robots_txt, user_agent)
        )
        if not blocked_crawlers:
            return None

        return {
            "reason_code": AI_CRAWLER_BLOCKED,
            "evidence": [
                {
                    "check": "blocked_ai_crawlers",
                    "value": blocked_crawlers,
                    "source": "robots_txt",
                },
                {
                    "check": "blocked_ai_crawler_count",
                    "value": len(blocked_crawlers),
                    "source": "robots_txt",
                },
            ],
            "confidence": 0.95,
            "applicability": "web",
        }

    def _citation_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        items = _content_items(payload)
        if not items:
            return None

        citation_signals = _content_signal_count(items, "citations", "references", "cited_sources", "external_links")
        if citation_signals > 0:
            return None

        return {
            "reason_code": MISSING_CITATIONS,
            "evidence": [
                {
                    "check": "content_items",
                    "value": len(items),
                    "source": "content_parsing.items",
                },
                {
                    "check": "citation_signals",
                    "value": citation_signals,
                    "source": "content_parsing.items[].citations|references|cited_sources|external_links",
                },
            ],
            "confidence": 0.85,
            "applicability": "web",
        }

    def _statistics_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        items = _content_items(payload)
        if not items:
            return None

        statistics_signals = _content_signal_count(
            items,
            "statistics",
            "data_points",
            "numbers_count",
            "numerical_claims",
        )
        if statistics_signals > 0:
            return None

        return {
            "reason_code": MISSING_STATISTICS,
            "evidence": [
                {
                    "check": "content_items",
                    "value": len(items),
                    "source": "content_parsing.items",
                },
                {
                    "check": "statistics_signals",
                    "value": statistics_signals,
                    "source": "content_parsing.items[].statistics|data_points|numbers_count|numerical_claims",
                },
            ],
            "confidence": 0.85,
            "applicability": "web",
        }

    def _quotation_finding(self, payload: Mapping[str, object]) -> OnPageFinding | None:
        items = _content_items(payload)
        if not items:
            return None

        quotation_signals = _content_signal_count(
            items,
            "quotations",
            "expert_quotes",
            "blockquotes",
            "testimonials",
        )
        if quotation_signals > 0:
            return None

        return {
            "reason_code": MISSING_QUOTATIONS,
            "evidence": [
                {
                    "check": "content_items",
                    "value": len(items),
                    "source": "content_parsing.items",
                },
                {
                    "check": "quotation_signals",
                    "value": quotation_signals,
                    "source": "content_parsing.items[].quotations|expert_quotes|blockquotes|testimonials",
                },
            ],
            "confidence": 0.85,
            "applicability": "web",
        }


def _summary_checks(payload: Mapping[str, object]) -> Mapping[str, object]:
    summary = _section(payload, "summary")
    page_metrics = _mapping(summary.get("page_metrics"))
    checks = _mapping(page_metrics.get("checks"))
    if checks:
        return checks

    page_metrics = _mapping(payload.get("page_metrics"))
    checks = _mapping(page_metrics.get("checks"))
    return checks


def _robots_txt_content(payload: Mapping[str, object]) -> str:
    direct = _extract_robots_text(payload.get("robots_txt"))
    if direct:
        return direct

    crawl_access = _mapping(payload.get("crawl_access"))
    crawl_access_direct = _extract_robots_text(crawl_access.get("robots_txt"))
    if crawl_access_direct:
        return crawl_access_direct
    crawl_access_content = _extract_robots_text(crawl_access)
    if crawl_access_content:
        return crawl_access_content

    technical = _section(payload, "technical")
    technical_robots = _extract_robots_text(technical.get("robots_txt"))
    if technical_robots:
        return technical_robots
    return ""


def _extract_robots_text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()

    mapping = _mapping(value)
    if not mapping:
        return ""

    for key in ("content", "text", "raw", "robots_txt"):
        candidate = mapping.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _is_user_agent_disallowed(robots_txt: str, user_agent: str) -> bool:
    normalized_agent = user_agent.strip().lower()
    parsed_rules = _parse_robots_groups(robots_txt)

    exact_disallow_paths: list[str] = []
    wildcard_disallow_paths: list[str] = []
    for agents, directives in parsed_rules:
        disallow_paths = [value for directive, value in directives if directive == "disallow" and value]
        if not disallow_paths:
            continue

        if normalized_agent in agents:
            exact_disallow_paths.extend(disallow_paths)
        elif "*" in agents:
            wildcard_disallow_paths.extend(disallow_paths)

    if exact_disallow_paths:
        return True
    return bool(wildcard_disallow_paths)


def _parse_robots_groups(robots_txt: str) -> list[tuple[set[str], list[tuple[str, str]]]]:
    groups: list[tuple[set[str], list[tuple[str, str]]]] = []
    current_agents: set[str] = set()
    current_directives: list[tuple[str, str]] = []

    for raw_line in robots_txt.splitlines():
        line = raw_line.split("#", maxsplit=1)[0].strip()
        if not line or ":" not in line:
            continue

        directive, value = line.split(":", maxsplit=1)
        normalized_directive = directive.strip().lower()
        normalized_value = value.strip().lower()
        if not normalized_directive:
            continue

        if normalized_directive == "user-agent":
            if current_directives:
                groups.append((set(current_agents), list(current_directives)))
                current_agents.clear()
                current_directives.clear()
            if normalized_value:
                current_agents.add(normalized_value)
            continue

        if not current_agents:
            continue

        current_directives.append((normalized_directive, normalized_value))

    if current_agents:
        groups.append((set(current_agents), list(current_directives)))
    return groups


def _microdata_items(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    section = _section(payload, "microdata")
    items = _items(section)
    if items:
        return items

    direct_items = _items(payload)
    return [item for item in direct_items if _schema_types(item)]


def _content_items(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    section = _section(payload, "content_parsing")
    items = _items(section)
    if items:
        return items

    direct_items = _items(payload)
    return [item for item in direct_items if _content_word_count(item) > 0 or _content_signal_present(item)]


def _content_signal_present(item: Mapping[str, object]) -> bool:
    return any(key in item for key in ("faq_sections", "faq_count", "tables", "table_count", "data_tables"))


def _content_signal_count(items: Sequence[Mapping[str, object]], *keys: str) -> float:
    return sum(_as_signal_count(item.get(key)) for item in items for key in keys)


def _content_word_count(item: Mapping[str, object]) -> int:
    return int(_first_number(item, "plain_text_word_count", "word_count", "content_length"))


def _schema_types(item: Mapping[str, object]) -> list[str]:
    values: list[str] = []
    for key in ("types", "type"):
        raw = item.get(key)
        if isinstance(raw, str) and raw.strip():
            values.append(raw.strip())
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            for entry in raw:
                if isinstance(entry, str) and entry.strip():
                    values.append(entry.strip())

    nested_microdata = item.get("microdata")
    if isinstance(nested_microdata, Sequence) and not isinstance(nested_microdata, (str, bytes)):
        for entry in nested_microdata:
            if isinstance(entry, Mapping):
                values.extend(_schema_types(cast(Mapping[str, object], entry)))

    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            unique_values.append(normalized)
            seen.add(normalized)
    return unique_values


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


def _first_number(item: Mapping[str, object], *keys: str) -> float:
    for key in keys:
        value = _as_number(item.get(key))
        if value:
            return value
    return 0.0


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


def _as_signal_count(value: object) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    if isinstance(value, str):
        return 1.0 if value.strip() else 0.0
    if isinstance(value, Mapping):
        return 1.0 if value else 0.0
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return float(len(value))
    return 0.0
