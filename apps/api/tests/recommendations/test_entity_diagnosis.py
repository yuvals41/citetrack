from __future__ import annotations

from typing import cast

from ai_visibility.diagnosis.entity import (
    AMBIGUOUS_BRAND,
    ENTITY_CLARITY_WEAK,
    KG_PRESENCE_MISSING,
    EntityDiagnoser,
    EntityFinding,
)


def test_entity_ingest_ambiguous_brand_for_local_and_non_local_brands() -> None:
    payload: dict[str, object] = {
        "brand_disambiguation": {
            "generic_brand": True,
            "ambiguity_score": 0.88,
            "same_named_entities": 4,
            "exact_match_confidence": 0.34,
            "same_as": ["https://example.com/about"],
        },
        "knowledge_graph": {
            "present": True,
            "url": "https://g.co/kgs/example-brand",
            "confidence": 0.38,
        },
        "wikidata": {
            "present": True,
            "qid": "Q12345",
        },
    }

    for is_local_brand in (False, True):
        findings = [
            cast(EntityFinding, cast(object, finding))
            for finding in EntityDiagnoser().ingest(payload, is_local_brand=is_local_brand)
        ]

        assert {finding["reason_code"] for finding in findings} == {
            AMBIGUOUS_BRAND,
            ENTITY_CLARITY_WEAK,
        }
        for finding in findings:
            assert finding["applicability"] == "all"
            assert 0.0 <= finding["confidence"] <= 1.0
            assert finding["evidence"]
            for evidence in finding["evidence"]:
                assert set(evidence.keys()) == {"check", "value", "source"}


def test_entity_ingest_kg_presence_missing() -> None:
    payload: dict[str, object] = {
        "brand_disambiguation": {
            "tasks": [
                {
                    "status_code": 20000,
                    "result": [
                        {
                            "exact_match_confidence": 0.91,
                            "same_as": [
                                "https://example.com/",
                                "https://www.linkedin.com/company/example",
                                "https://www.crunchbase.com/organization/example",
                            ],
                        }
                    ],
                }
            ]
        },
        "knowledge_graph": {},
        "wikidata": {},
    }

    findings = [cast(EntityFinding, cast(object, finding)) for finding in EntityDiagnoser().ingest(payload)]

    assert len(findings) == 1
    assert findings[0]["reason_code"] == KG_PRESENCE_MISSING
    assert findings[0]["applicability"] == "all"


def test_entity_non_local_brand_skips_local_penalties() -> None:
    payload: dict[str, object] = {
        "brand_disambiguation": {
            "exact_match_confidence": 0.92,
            "same_as": [
                "https://example.com/",
                "https://www.linkedin.com/company/example",
                "https://www.crunchbase.com/organization/example",
            ],
        },
        "knowledge_graph": {
            "present": True,
            "url": "https://g.co/kgs/example-brand",
            "confidence": 0.84,
        },
        "wikidata": {
            "present": True,
            "qid": "Q54321",
        },
        "local_presence": {
            "listing_count": 0,
        },
        "reputation": {
            "review_count": 0,
            "average_rating": 0.0,
        },
    }

    non_local_findings = EntityDiagnoser().ingest(payload, is_local_brand=False)
    local_findings = [
        cast(EntityFinding, cast(object, finding)) for finding in EntityDiagnoser().ingest(payload, is_local_brand=True)
    ]

    assert non_local_findings == []
    assert {finding["reason_code"] for finding in local_findings} == {ENTITY_CLARITY_WEAK}
    clarity = local_findings[0]
    checks = {evidence["check"] for evidence in clarity["evidence"]}
    assert {"local_listing_count", "review_count", "average_rating"}.issubset(checks)


def test_entity_ingest_empty_payload() -> None:
    assert EntityDiagnoser().ingest({}) == []


def test_entity_ingest_unwraps_task_envelopes() -> None:
    payload: dict[str, object] = {
        "tasks": [
            {
                "status_code": 20000,
                "result": [
                    {
                        "brand_disambiguation": {
                            "generic_brand": True,
                            "ambiguity_score": 0.74,
                            "same_named_entities": 3,
                            "exact_match_confidence": 0.41,
                        },
                        "knowledge_graph": {"present": True, "url": "https://g.co/kgs/example-brand"},
                        "wikidata": {"present": True, "qid": "Q67890"},
                    }
                ],
            }
        ]
    }

    findings = [cast(EntityFinding, cast(object, finding)) for finding in EntityDiagnoser().ingest(payload)]

    assert {finding["reason_code"] for finding in findings} == {
        AMBIGUOUS_BRAND,
        ENTITY_CLARITY_WEAK,
    }
