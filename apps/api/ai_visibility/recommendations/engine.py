from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict, cast

from pydantic import BaseModel

from ai_visibility.models import RunResult
from ai_visibility.prompts import DEFAULT_PROMPTS
from ai_visibility.recommendations.findings import CANONICAL_REASON_CODES

COMPETITOR_WINS = "COMPETITOR_WINS"
MISSING_CITATIONS = "MISSING_CITATIONS"
LOW_VISIBILITY = "LOW_VISIBILITY"
PROMPT_CATEGORY_GAP = "PROMPT_CATEGORY_GAP"

Priority = Literal["high", "medium", "low"]
REQUIRED_PROMPT_CATEGORIES = {prompt["category"] for prompt in DEFAULT_PROMPTS}
RULES_VERSION = "v2"


class RecommendationRule(TypedDict):
    recommendation_code: str
    reason: str
    impact: str
    next_step: str


RECOMMENDATION_RULES: dict[str, RecommendationRule] = {
    "ai_crawler_blocked": {
        "recommendation_code": "unblock_ai_crawlers",
        "reason": "AI crawlers (GPTBot, PerplexityBot, etc.) are blocked in robots.txt",
        "impact": "Blocked crawlers cannot index content, making AI citation impossible — this is a binary gate",
        "next_step": "Update robots.txt to allow GPTBot, OAI-SearchBot, PerplexityBot, Google-Extended, and ClaudeBot",
    },
    "schema_missing": {
        "recommendation_code": "add_schema_markup",
        "reason": "No schema markup detected; AI engines cannot extract structured facts",
        "impact": "Missing schema reduces AI citation probability by ~40%",
        "next_step": "Add FAQ, HowTo, or Organization schema to key landing pages",
    },
    "content_answer_gap": {
        "recommendation_code": "fill_content_answer_gaps",
        "reason": "Content does not answer the AI-detected queries for this category",
        "impact": "Unanswered queries result in competitor citations instead of yours",
        "next_step": "Create or expand FAQ sections addressing the detected query gaps",
    },
    "missing_citations": {
        "recommendation_code": "add_cited_sources",
        "reason": "Content lacks cited sources and references",
        "impact": "Adding cited sources improves AI citation probability by 115-141% (GEO research)",
        "next_step": "Add inline citations, reference links, and source attributions to key content pages",
    },
    "missing_statistics": {
        "recommendation_code": "add_statistics",
        "reason": "Content lacks data points, numbers, and statistical evidence",
        "impact": "Adding statistics improves AI citation probability by 37-78% (GEO research)",
        "next_step": "Include specific numbers, percentages, and data-backed claims in content",
    },
    "missing_quotations": {
        "recommendation_code": "add_expert_quotations",
        "reason": "Content lacks expert quotes and testimonials",
        "impact": "Adding quotations improves AI citation probability by 112-115% (GEO research)",
        "next_step": "Add expert quotes, customer testimonials, and attributed statements to content pages",
    },
    "technical_barrier": {
        "recommendation_code": "fix_technical_barriers",
        "reason": "Crawl errors or redirect chains prevent AI indexing",
        "impact": "Technical barriers block content from being cited by any AI provider",
        "next_step": "Fix 4xx/5xx errors and remove unnecessary redirect chains",
    },
    "backlink_gap": {
        "recommendation_code": "build_authority_backlinks",
        "reason": "Low referring domain count compared to cited competitors",
        "impact": "Authority gap reduces trust signals used by AI for citation selection",
        "next_step": "Build 5-10 topically relevant backlinks from authoritative sources",
    },
    "grounded_search_authority_weak": {
        "recommendation_code": "strengthen_grounded_authority",
        "reason": "Brand authority is weak in grounded search provider results",
        "impact": "Weak authority in grounded search reduces citation frequency in web-search AI",
        "next_step": "Publish authoritative long-form content and earn press/media mentions",
    },
    "competitor_gap": {
        "recommendation_code": "close_competitor_authority_gap",
        "reason": "Competitor domain authority significantly exceeds yours",
        "impact": "Authority gap causes competitors to appear in AI responses instead of you",
        "next_step": "Analyze competitor backlink profiles and target their referring domains",
    },
    "entity_clarity_weak": {
        "recommendation_code": "clarify_brand_entity",
        "reason": "Brand entity is unclear or ambiguous to AI knowledge graphs",
        "impact": "Unclear entity reduces AI confidence in citing your brand accurately",
        "next_step": "Add Organization schema with sameAs links to authoritative profiles",
    },
    "ambiguous_brand": {
        "recommendation_code": "disambiguate_brand_name",
        "reason": "Brand name is ambiguous and may be confused with other entities",
        "impact": "Ambiguous brand names cause AI to skip or confuse your citations",
        "next_step": "Use distinctive brand descriptors in all content and schema markup",
    },
    "kg_presence_missing": {
        "recommendation_code": "establish_knowledge_graph_presence",
        "reason": "Brand has no detectable Knowledge Graph presence",
        "impact": "Absent from Knowledge Graph means AI cannot verify your entity claims",
        "next_step": "Create/claim Wikipedia, Wikidata, and Google Business Profile entries",
    },
}


_CANONICAL_REASON_CODES_SET = set(CANONICAL_REASON_CODES)


class Recommendation(BaseModel):
    rule_code: str
    title: str
    description: str
    priority: Priority
    workspace_slug: str


class RecommendationResult(BaseModel):
    recommendation_code: str
    reason: str
    evidence_refs: list[dict[str, object]]
    impact: str
    next_step: str
    confidence: float
    rules_version: str
    applicability: str


class RecommendationsEngine:
    def generate_from_findings(self, findings: list[dict[str, object]]) -> list[RecommendationResult]:
        if not findings:
            return []

        recommendations: list[RecommendationResult] = []
        for raw_finding in cast(list[object], findings):
            if not isinstance(raw_finding, Mapping):
                continue
            finding = cast(Mapping[str, object], raw_finding)

            reason_code_raw = finding.get("reason_code")
            if not isinstance(reason_code_raw, str):
                continue
            reason_code = reason_code_raw.strip()
            if not reason_code:
                continue
            if reason_code not in _CANONICAL_REASON_CODES_SET:
                continue

            rule = RECOMMENDATION_RULES.get(reason_code)
            if rule is None:
                continue

            recommendations.append(
                RecommendationResult(
                    recommendation_code=rule["recommendation_code"],
                    reason=rule["reason"],
                    evidence_refs=self._copy_evidence(finding.get("evidence")),
                    impact=rule["impact"],
                    next_step=rule["next_step"],
                    confidence=self._as_confidence(finding.get("confidence")),
                    rules_version=RULES_VERSION,
                    applicability=self._as_applicability(finding.get("applicability")),
                )
            )

        return recommendations

    def generate(self, workspace_slug: str, runs: list[RunResult]) -> list[Recommendation]:
        if not runs:
            return []

        recommendations: list[Recommendation] = []

        competitor_win_runs = sum(1 for run in runs if self._number(run, "competitor_wins") > 0)
        if competitor_win_runs >= 2:
            recommendations.append(
                Recommendation(
                    rule_code=COMPETITOR_WINS,
                    title="Competitors are repeatedly outranking your brand",
                    description=(
                        f"Competitors won in {competitor_win_runs} recent runs. "
                        "Update prompts to require direct brand comparison and proof points."
                    ),
                    priority="high",
                    workspace_slug=workspace_slug,
                )
            )

        missing_citation_runs = sum(
            1
            for run in runs
            if self._number(run, "missing_citations") > 0 or self._number(run, "citation_coverage") < 0.5
        )
        if missing_citation_runs > 0:
            recommendations.append(
                Recommendation(
                    rule_code=MISSING_CITATIONS,
                    title="Citation coverage is weak",
                    description=(
                        f"{missing_citation_runs} recent runs show missing or weak citations. "
                        "Improve sourceable claims and add citation-oriented prompts."
                    ),
                    priority="medium",
                    workspace_slug=workspace_slug,
                )
            )

        visibility_scores = [
            self._number(run, "visibility_score") for run in runs if self._has_value(run, "visibility_score")
        ]
        if visibility_scores:
            average_visibility = sum(visibility_scores) / len(visibility_scores)
            if average_visibility < 0.4:
                recommendations.append(
                    Recommendation(
                        rule_code=LOW_VISIBILITY,
                        title="Overall visibility is low",
                        description=(
                            f"Average visibility score is {average_visibility:.2f}. "
                            "Focus on high-intent prompts and stronger brand positioning language."
                        ),
                        priority="high",
                        workspace_slug=workspace_slug,
                    )
                )

        categories_seen = {
            str(category).strip().lower() for run in runs for category in self._categories(run) if str(category).strip()
        }
        if categories_seen:
            missing_categories = sorted(REQUIRED_PROMPT_CATEGORIES - categories_seen)
            if missing_categories:
                recommendations.append(
                    Recommendation(
                        rule_code=PROMPT_CATEGORY_GAP,
                        title="Prompt category coverage has gaps",
                        description=(
                            "Missing prompt categories: "
                            + ", ".join(missing_categories)
                            + ". Add prompts for each category to balance visibility signals."
                        ),
                        priority="low",
                        workspace_slug=workspace_slug,
                    )
                )

        return recommendations

    def _categories(self, run: RunResult) -> list[str]:
        value = self._value(run, "prompt_category")
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            items = cast(list[object], value)
            return [str(item) for item in items]
        return []

    def _number(self, run: RunResult, key: str) -> float:
        value = self._value(run, key)
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def _has_value(self, run: RunResult, key: str) -> bool:
        return self._value(run, key) is not None

    def _value(self, run: RunResult, key: str) -> object | None:
        if isinstance(run, dict):
            return cast(dict[str, object], run).get(key)
        return getattr(run, key, None)

    def _copy_evidence(self, raw: object) -> list[dict[str, object]]:
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            return []

        copied: list[dict[str, object]] = []
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            copied.append(dict(cast(Mapping[str, object], item)))
        return copied

    def _as_confidence(self, raw: object) -> float:
        if isinstance(raw, bool):
            return 1.0 if raw else 0.0
        if isinstance(raw, (int, float)):
            return max(0.0, min(1.0, float(raw)))
        return 0.0

    def _as_applicability(self, raw: object) -> str:
        if not isinstance(raw, str):
            return "all"
        normalized = raw.strip().lower()
        if normalized in {"all", "grounded_search"}:
            return normalized
        return "all"
