from __future__ import annotations

from ai_visibility.recommendations import FindingsPipeline


def test_findings_pipeline_generate_merges_duplicate_reason_codes() -> None:
    diagnosis_results: list[dict[str, object]] = [
        {
            "reason_code": "backlink_gap",
            "evidence": [
                {
                    "check": "referring_domains",
                    "value": 12,
                    "source": "summary.referring_domains",
                }
            ],
            "confidence": 0.56,
            "applicability": "all",
        },
        {
            "reason_code": "backlink_gap",
            "evidence": [
                {
                    "check": "referring_domain_threshold",
                    "value": 30,
                    "source": "rule.backlink_gap.referring_domains",
                },
                {
                    "check": "referring_domains",
                    "value": 12,
                    "source": "summary.referring_domains",
                },
            ],
            "confidence": 0.82,
            "applicability": "all",
        },
    ]

    findings = FindingsPipeline().generate(diagnosis_results)

    assert len(findings) == 1
    assert findings[0]["reason_code"] == "backlink_gap"
    assert findings[0]["confidence"] == 0.82
    assert findings[0]["applicability"] == "all"
    assert findings[0]["evidence"] == [
        {
            "check": "referring_domains",
            "value": 12,
            "source": "summary.referring_domains",
        },
        {
            "check": "referring_domain_threshold",
            "value": 30,
            "source": "rule.backlink_gap.referring_domains",
        },
    ]


def test_findings_pipeline_generate_orders_by_confidence_descending() -> None:
    diagnosis_results: list[dict[str, object]] = [
        {
            "reason_code": "schema_missing",
            "evidence": [{"check": "microdata_items", "value": 0, "source": "microdata.items"}],
            "confidence": 0.35,
            "applicability": "all",
        },
        {
            "reason_code": "kg_presence_missing",
            "evidence": [{"check": "knowledge_graph_present", "value": False, "source": "knowledge_graph.present"}],
            "confidence": 0.8,
            "applicability": "all",
        },
        {
            "reason_code": "grounded_search_authority_weak",
            "evidence": [
                {
                    "check": "authoritative_citations",
                    "value": 0,
                    "source": "authority_signals.grounded_search.authoritative_citations",
                }
            ],
            "confidence": 0.61,
            "applicability": "grounded_search",
        },
    ]

    findings = FindingsPipeline().generate(diagnosis_results)

    assert [finding["reason_code"] for finding in findings] == [
        "kg_presence_missing",
        "grounded_search_authority_weak",
        "schema_missing",
    ]
    assert [finding["confidence"] for finding in findings] == [0.8, 0.61, 0.35]


def test_findings_pipeline_generate_normalizes_web_applicability_to_all() -> None:
    diagnosis_results: list[dict[str, object]] = [
        {
            "reason_code": "technical_barrier",
            "evidence": [{"check": "is_5xx_code", "value": 1, "source": "summary.page_metrics.checks.is_5xx_code"}],
            "confidence": 0.73,
            "applicability": "web",
        }
    ]

    findings = FindingsPipeline().generate(diagnosis_results)

    assert findings == [
        {
            "reason_code": "technical_barrier",
            "evidence": [
                {
                    "check": "is_5xx_code",
                    "value": 1,
                    "source": "summary.page_metrics.checks.is_5xx_code",
                }
            ],
            "confidence": 0.73,
            "applicability": "all",
        }
    ]


def test_findings_pipeline_sparse_inputs_returns_empty_list() -> None:
    diagnosis_results: list[dict[str, object]] = [
        {},
        {"reason_code": "", "evidence": [], "confidence": 0.4, "applicability": "all"},
        {"reason_code": "entity_clarity_weak", "evidence": "not-a-list", "confidence": "0.9", "applicability": 7},
        {"reason_code": None, "evidence": [], "confidence": 0.2, "applicability": "all"},
    ]

    findings = FindingsPipeline().generate(diagnosis_results)

    assert findings == [
        {
            "reason_code": "entity_clarity_weak",
            "evidence": [],
            "confidence": 0.0,
            "applicability": "all",
        }
    ]


def test_findings_pipeline_generate_empty_input_returns_empty_list() -> None:
    assert FindingsPipeline().generate([]) == []
