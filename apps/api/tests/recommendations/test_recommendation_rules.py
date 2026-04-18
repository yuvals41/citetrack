from __future__ import annotations

from ai_visibility.recommendations import CANONICAL_REASON_CODES
from ai_visibility.recommendations.engine import RULES_VERSION, RecommendationsEngine


def _finding(
    reason_code: str,
    *,
    evidence: list[dict[str, object]] | None = None,
    confidence: float = 0.73,
    applicability: str = "all",
) -> dict[str, object]:
    return {
        "reason_code": reason_code,
        "evidence": evidence
        if evidence is not None
        else [{"check": "sample_check", "value": "sample_value", "source": "fixture"}],
        "confidence": confidence,
        "applicability": applicability,
    }


def test_recommendation_rules_happy_path_for_all_canonical_reason_codes() -> None:
    expected_codes = {
        "ai_crawler_blocked": "unblock_ai_crawlers",
        "schema_missing": "add_schema_markup",
        "content_answer_gap": "fill_content_answer_gaps",
        "missing_citations": "add_cited_sources",
        "missing_statistics": "add_statistics",
        "missing_quotations": "add_expert_quotations",
        "technical_barrier": "fix_technical_barriers",
        "backlink_gap": "build_authority_backlinks",
        "grounded_search_authority_weak": "strengthen_grounded_authority",
        "competitor_gap": "close_competitor_authority_gap",
        "entity_clarity_weak": "clarify_brand_entity",
        "ambiguous_brand": "disambiguate_brand_name",
        "kg_presence_missing": "establish_knowledge_graph_presence",
    }
    findings = [_finding(reason_code) for reason_code in CANONICAL_REASON_CODES]

    recommendations = RecommendationsEngine().generate_from_findings(findings)

    assert RULES_VERSION == "v2"
    assert len(recommendations) == len(CANONICAL_REASON_CODES)
    for recommendation in recommendations:
        assert recommendation.recommendation_code in expected_codes.values()
        assert recommendation.reason
        assert recommendation.impact
        assert recommendation.next_step
        assert recommendation.rules_version == RULES_VERSION
        assert recommendation.applicability == "all"
        assert 0.0 <= recommendation.confidence <= 1.0

    recommendation_by_code = {recommendation.recommendation_code: recommendation for recommendation in recommendations}
    for reason_code, recommendation_code in expected_codes.items():
        assert recommendation_code in recommendation_by_code, reason_code


def test_recommendation_rules_include_evidence_refs_when_evidence_present() -> None:
    evidence: list[dict[str, object]] = [
        {
            "check": "schema_presence",
            "value": 0,
            "source": "onpage",
        }
    ]
    findings = [_finding("schema_missing", evidence=evidence, confidence=0.81, applicability="grounded_search")]

    recommendations = RecommendationsEngine().generate_from_findings(findings)

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.evidence_refs == evidence
    assert recommendation.applicability == "grounded_search"
    assert recommendation.confidence == 0.81


def test_recommendation_rules_missing_evidence_list_is_valid() -> None:
    findings = [_finding("entity_clarity_weak", evidence=[])]

    recommendations = RecommendationsEngine().generate_from_findings(findings)

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.recommendation_code == "clarify_brand_entity"
    assert recommendation.evidence_refs == []


def test_recommendation_rules_unknown_reason_code_is_skipped() -> None:
    findings = [_finding("not_a_known_reason"), _finding("schema_missing")]

    recommendations = RecommendationsEngine().generate_from_findings(findings)

    assert len(recommendations) == 1
    assert recommendations[0].recommendation_code == "add_schema_markup"


def test_recommendation_rules_returns_empty_for_empty_or_malformed_findings() -> None:
    engine = RecommendationsEngine()

    assert engine.generate_from_findings([]) == []
    assert engine.generate_from_findings([{"evidence": []}, {"reason_code": "   "}, {"reason_code": 3}]) == []
