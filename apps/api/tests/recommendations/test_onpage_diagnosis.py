from __future__ import annotations

from typing import cast

from ai_visibility.diagnosis import (
    AI_CRAWLER_BLOCKED,
    CONTENT_ANSWER_GAP,
    MISSING_CITATIONS,
    MISSING_QUOTATIONS,
    MISSING_STATISTICS,
    OnPageFinding,
    SCHEMA_MISSING,
    TECHNICAL_BARRIER,
    OnPageDiagnoser,
)


def test_ingest_normalizes_onpage_payload_into_expected_findings() -> None:
    payload: dict[str, object] = {
        "summary": {
            "page_metrics": {
                "checks": {
                    "is_4xx_code": 2,
                    "is_redirect_chain": 1,
                }
            }
        },
        "microdata": {
            "items": [
                {"url": "https://example.com/", "types": ["WebPage"]},
                {"url": "https://example.com/pricing", "types": ["Organization"]},
            ]
        },
        "content_parsing": {
            "items": [
                {
                    "url": "https://example.com/pricing",
                    "plain_text_word_count": 92,
                    "faq_sections": 0,
                    "tables": 0,
                },
                {
                    "url": "https://example.com/compare",
                    "plain_text_word_count": 108,
                    "faq_sections": 0,
                    "tables": 0,
                },
            ]
        },
        "technical": {
            "broken_pages": [{"url": "https://example.com/missing", "status_code": 404}],
            "redirect_chains": [{"url": "http://example.com", "chain": [1, 2]}],
        },
    }

    findings = OnPageDiagnoser().ingest(payload)
    typed_findings = [cast(OnPageFinding, cast(object, finding)) for finding in findings]

    assert {finding["reason_code"] for finding in typed_findings} == {
        SCHEMA_MISSING,
        CONTENT_ANSWER_GAP,
        MISSING_CITATIONS,
        MISSING_STATISTICS,
        MISSING_QUOTATIONS,
        TECHNICAL_BARRIER,
    }
    for finding in typed_findings:
        assert finding["applicability"] == "web"
        assert 0.0 <= finding["confidence"] <= 1.0
        assert finding["evidence"]
        for evidence in finding["evidence"]:
            assert set(evidence.keys()) == {"check", "value", "source"}


def test_ingest_sparse_schema_emits_low_confidence_schema_missing_finding() -> None:
    payload: dict[str, object] = {
        "summary": {"page_metrics": {"checks": {}}},
        "microdata": {"items": []},
        "content_parsing": {"items": []},
        "technical": {},
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    assert len(findings) == 1
    assert findings[0]["reason_code"] == SCHEMA_MISSING
    assert findings[0]["confidence"] <= 0.5
    assert findings[0]["evidence"][0] == {
        "check": "microdata_items",
        "value": 0,
        "source": "microdata.items",
    }


def test_ingest_detects_technical_barrier_from_summary_and_detail_evidence() -> None:
    payload: dict[str, object] = {
        "summary": {
            "page_metrics": {
                "checks": {
                    "is_5xx_code": 1,
                    "is_broken": 3,
                }
            }
        },
        "technical": {
            "broken_pages": [
                {"url": "https://example.com/outage", "status_code": 500},
                {"url": "https://example.com/timeout", "status_code": 503},
            ]
        },
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    technical = next(finding for finding in findings if finding["reason_code"] == TECHNICAL_BARRIER)
    checks = {evidence["check"] for evidence in technical["evidence"]}
    assert {"is_5xx_code", "is_broken", "broken_pages"}.issubset(checks)
    assert technical["confidence"] >= 0.75


def test_ingest_detects_ai_crawler_blocked_from_robots_txt() -> None:
    payload: dict[str, object] = {
        "robots_txt": "User-agent: GPTBot\nDisallow: /\n",
        "microdata": {"items": [{"types": ["FAQPage"]}]},
        "content_parsing": {
            "items": [
                {
                    "plain_text_word_count": 240,
                    "faq_sections": 2,
                    "tables": 1,
                    "external_links": ["https://example.com/source"],
                    "numbers_count": 3,
                    "quotations": ["Expert says"],
                }
            ]
        },
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    ai_finding = next(finding for finding in findings if finding["reason_code"] == AI_CRAWLER_BLOCKED)
    assert ai_finding["confidence"] == 0.95
    blocked = next(evidence for evidence in ai_finding["evidence"] if evidence["check"] == "blocked_ai_crawlers")
    assert "GPTBot" in cast(list[str], blocked["value"])


def test_ingest_no_ai_crawler_finding_when_all_allowed() -> None:
    payload: dict[str, object] = {
        "robots_txt": "\n".join(
            [
                "User-agent: GPTBot",
                "Disallow:",
                "User-agent: OAI-SearchBot",
                "Disallow:",
                "User-agent: PerplexityBot",
                "Disallow:",
                "User-agent: Google-Extended",
                "Disallow:",
                "User-agent: ClaudeBot",
                "Disallow:",
                "User-agent: CCBot",
                "Disallow:",
            ]
        ),
        "microdata": {"items": [{"types": ["FAQPage"]}]},
        "content_parsing": {
            "items": [
                {
                    "plain_text_word_count": 240,
                    "faq_sections": 2,
                    "tables": 1,
                    "external_links": ["https://example.com/source"],
                    "numbers_count": 3,
                    "quotations": ["Expert says"],
                }
            ]
        },
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    assert all(finding["reason_code"] != AI_CRAWLER_BLOCKED for finding in findings)


def test_ingest_detects_missing_citations() -> None:
    payload: dict[str, object] = {
        "content_parsing": {
            "items": [
                {
                    "plain_text_word_count": 240,
                    "faq_sections": 1,
                    "tables": 1,
                    "numbers_count": 2,
                    "quotations": ["Founder quote"],
                }
            ]
        }
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    assert any(finding["reason_code"] == MISSING_CITATIONS for finding in findings)


def test_ingest_detects_missing_statistics() -> None:
    payload: dict[str, object] = {
        "content_parsing": {
            "items": [
                {
                    "plain_text_word_count": 240,
                    "faq_sections": 1,
                    "tables": 1,
                    "external_links": ["https://example.com/source"],
                    "quotations": ["Founder quote"],
                }
            ]
        }
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    assert any(finding["reason_code"] == MISSING_STATISTICS for finding in findings)


def test_ingest_detects_missing_quotations() -> None:
    payload: dict[str, object] = {
        "content_parsing": {
            "items": [
                {
                    "plain_text_word_count": 240,
                    "faq_sections": 1,
                    "tables": 1,
                    "external_links": ["https://example.com/source"],
                    "numbers_count": 4,
                }
            ]
        }
    }

    findings = [cast(OnPageFinding, cast(object, finding)) for finding in OnPageDiagnoser().ingest(payload)]

    assert any(finding["reason_code"] == MISSING_QUOTATIONS for finding in findings)
