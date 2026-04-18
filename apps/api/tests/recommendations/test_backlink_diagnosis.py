from __future__ import annotations

from typing import cast

from ai_visibility.diagnosis.backlinks import (
    BACKLINK_GAP,
    COMPETITOR_GAP,
    GROUNDED_SEARCH_AUTHORITY_WEAK,
    BacklinkDiagnoser,
    BacklinkFinding,
)


def test_backlink_ingest_normalizes_expected_findings() -> None:
    payload: dict[str, object] = {
        "summary": {
            "referring_domains": 12,
            "domain_rank": 24,
        },
        "authority_signals": {
            "grounded_search": {
                "providers": ["perplexity", "claude_web_search"],
                "authoritative_referring_domains": 1,
                "authoritative_citations": 0,
            },
            "is_local_brand": False,
            "generic_llm_visibility": {"share_of_voice": 0.05},
        },
        "competitor_gap": {
            "target": {"domain": "example.com", "referring_domains": 12},
            "competitors": [
                {"domain": "leader.example", "referring_domains": 120},
                {"domain": "challenger.example", "referring_domains": 74},
            ],
        },
    }

    findings = BacklinkDiagnoser().ingest(payload)
    typed_findings = [cast(BacklinkFinding, cast(object, finding)) for finding in findings]

    assert {finding["reason_code"] for finding in typed_findings} == {
        BACKLINK_GAP,
        GROUNDED_SEARCH_AUTHORITY_WEAK,
        COMPETITOR_GAP,
    }
    for finding in typed_findings:
        assert 0.0 <= finding["confidence"] <= 1.0
        assert finding["evidence"]
        for evidence in finding["evidence"]:
            assert set(evidence.keys()) == {"check", "value", "source"}

    grounded_authority = next(
        finding for finding in typed_findings if finding["reason_code"] == GROUNDED_SEARCH_AUTHORITY_WEAK
    )
    assert grounded_authority["applicability"] == "grounded_search"

    backlink_gap = next(finding for finding in typed_findings if finding["reason_code"] == BACKLINK_GAP)
    assert backlink_gap["applicability"] == "all"


def test_backlink_ingest_unwraps_task_envelopes() -> None:
    payload: dict[str, object] = {
        "summary": {
            "tasks": [
                {
                    "status_code": 20000,
                    "result": [{"referring_domains": 18, "domain_rank": 31}],
                }
            ]
        },
        "authority_signals": {
            "grounded_search": {
                "tasks": [
                    {
                        "status_code": 20000,
                        "result": [
                            {
                                "providers": ["perplexity"],
                                "authoritative_referring_domains": 1,
                                "authoritative_citations": 1,
                            }
                        ],
                    }
                ]
            }
        },
        "competitor_gap": {
            "tasks": [
                {
                    "status_code": 20000,
                    "result": [
                        {
                            "target": {"referring_domains": 18},
                            "competitors": [{"domain": "winner.example", "referring_domains": 70}],
                        }
                    ],
                }
            ]
        },
    }

    findings = [cast(BacklinkFinding, cast(object, finding)) for finding in BacklinkDiagnoser().ingest(payload)]

    assert {finding["reason_code"] for finding in findings} == {
        BACKLINK_GAP,
        GROUNDED_SEARCH_AUTHORITY_WEAK,
        COMPETITOR_GAP,
    }


def test_backlink_grounded_authority_is_grounded_search_only() -> None:
    payload: dict[str, object] = {
        "summary": {"referring_domains": 28, "domain_rank": 45},
        "authority_signals": {
            "provider_modes": {
                "perplexity": "grounded_search",
                "chatgpt": "llm",
            },
            "authoritative_referring_domains": 1,
            "authoritative_citations": 0,
            "generic_llm_visibility": {"share_of_voice": 0.0},
            "is_local_brand": False,
        },
    }

    findings = [cast(BacklinkFinding, cast(object, finding)) for finding in BacklinkDiagnoser().ingest(payload)]

    grounded_authority = next(
        finding for finding in findings if finding["reason_code"] == GROUNDED_SEARCH_AUTHORITY_WEAK
    )
    providers_evidence = next(
        evidence for evidence in grounded_authority["evidence"] if evidence["check"] == "grounded_search_providers"
    )

    assert grounded_authority["applicability"] == "grounded_search"
    assert providers_evidence["value"] == ["perplexity"]


def test_backlink_grounded_authority_skips_local_penalty_for_non_local_brand() -> None:
    payload: dict[str, object] = {
        "summary": {"referring_domains": 85, "domain_rank": 62},
        "authority_signals": {
            "grounded_search": {
                "providers": ["perplexity"],
                "authoritative_referring_domains": 8,
                "authoritative_citations": 5,
                "local_authority_citations": 0,
            },
            "is_local_brand": False,
        },
    }

    findings = [cast(BacklinkFinding, cast(object, finding)) for finding in BacklinkDiagnoser().ingest(payload)]

    assert findings == []


def test_backlink_ingest_returns_empty_list_for_sparse_payload() -> None:
    assert BacklinkDiagnoser().ingest({}) == []
