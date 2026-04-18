from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, cast

ENTITY_CLARITY_WEAK = "entity_clarity_weak"
AMBIGUOUS_BRAND = "ambiguous_brand"
KG_PRESENCE_MISSING = "kg_presence_missing"

_AMBIGUITY_SCORE_THRESHOLD = 0.6
_LOW_BRAND_CONFIDENCE_THRESHOLD = 0.55
_LOW_KG_CONFIDENCE_THRESHOLD = 0.45
_MIN_SAME_AS_LINKS = 2.0
_MIN_LOCAL_LISTINGS = 1.0
_MIN_REVIEW_COUNT = 5.0
_MIN_REVIEW_RATING = 4.0


class FindingEvidence(TypedDict):
    check: str
    value: object
    source: str


class EntityFinding(TypedDict):
    reason_code: str
    evidence: list[FindingEvidence]
    confidence: float
    applicability: str


class LocalSignalSummary(TypedDict):
    evidence: list[FindingEvidence]
    weak_signals: int


class EntityDiagnoser:
    def ingest(self, payload: dict[str, object], is_local_brand: bool = False) -> list[dict[str, object]]:
        normalized_payload = _unwrap_task_result(cast(object, payload))
        if not normalized_payload or not _has_entity_context(normalized_payload):
            return []

        findings: list[EntityFinding] = []

        ambiguous_brand = self._ambiguous_brand_finding(normalized_payload)
        if ambiguous_brand is not None:
            findings.append(ambiguous_brand)

        entity_clarity = self._entity_clarity_finding(normalized_payload, is_local_brand=is_local_brand)
        if entity_clarity is not None:
            findings.append(entity_clarity)

        kg_presence = self._kg_presence_finding(normalized_payload)
        if kg_presence is not None:
            findings.append(kg_presence)

        return cast(list[dict[str, object]], findings)

    def _ambiguous_brand_finding(self, payload: Mapping[str, object]) -> EntityFinding | None:
        brand = _brand_section(payload)
        if not brand:
            return None

        generic_brand = _first_bool(brand, "generic_brand", "is_generic_name", "is_generic_brand")
        ambiguity_score = _first_number(
            brand,
            "ambiguity_score",
            "disambiguation_difficulty",
            "genericity_score",
            "brand_name_genericity",
        )
        candidate_entities = _candidate_count(brand)
        exact_match_confidence = _first_number(
            brand,
            "exact_match_confidence",
            "brand_confidence",
            "confidence",
            "disambiguation_confidence",
        )

        weak_signals = 0
        if generic_brand:
            weak_signals += 1
        if ambiguity_score >= _AMBIGUITY_SCORE_THRESHOLD:
            weak_signals += 1
        if candidate_entities > 1:
            weak_signals += 1
        if _has_any_key(brand, "exact_match_confidence", "brand_confidence", "confidence", "disambiguation_confidence"):
            if exact_match_confidence < _LOW_BRAND_CONFIDENCE_THRESHOLD:
                weak_signals += 1

        if weak_signals == 0:
            return None

        evidence: list[FindingEvidence] = [
            {
                "check": "generic_brand_name",
                "value": generic_brand,
                "source": "brand_disambiguation.generic_brand",
            },
            {
                "check": "ambiguity_score",
                "value": round(ambiguity_score, 2),
                "source": "brand_disambiguation.ambiguity_score",
            },
            {
                "check": "candidate_entities",
                "value": candidate_entities,
                "source": "brand_disambiguation.candidate_entities",
            },
            {
                "check": "exact_match_confidence",
                "value": round(exact_match_confidence, 2),
                "source": "brand_disambiguation.exact_match_confidence",
            },
        ]

        confidence = min(0.95, 0.43 + (weak_signals * 0.12) + (0.07 if generic_brand else 0.0))
        return {
            "reason_code": AMBIGUOUS_BRAND,
            "evidence": evidence,
            "confidence": confidence,
            "applicability": "all",
        }

    def _entity_clarity_finding(self, payload: Mapping[str, object], is_local_brand: bool) -> EntityFinding | None:
        brand = _brand_section(payload)
        knowledge_graph = _knowledge_graph_section(payload)
        wikidata = _wikidata_section(payload)
        if not brand and not knowledge_graph and not wikidata:
            return None

        same_as_links = _same_as_count(payload, brand, knowledge_graph, wikidata)
        candidate_entities = max(_candidate_count(brand), _candidate_count(knowledge_graph))
        brand_confidence_present = _has_any_key(
            brand,
            "exact_match_confidence",
            "brand_confidence",
            "confidence",
            "disambiguation_confidence",
        )
        brand_confidence = _first_number(
            brand,
            "exact_match_confidence",
            "brand_confidence",
            "confidence",
            "disambiguation_confidence",
        )
        kg_confidence_present = _has_any_key(
            knowledge_graph,
            "confidence",
            "score",
            "confidence_score",
            "relevance_score",
        )
        kg_confidence = _first_number(
            knowledge_graph,
            "confidence",
            "score",
            "confidence_score",
            "relevance_score",
        )

        evidence: list[FindingEvidence] = [
            {
                "check": "same_as_links",
                "value": same_as_links,
                "source": "brand_disambiguation.same_as",
            },
            {
                "check": "candidate_entities",
                "value": candidate_entities,
                "source": "brand_disambiguation.candidate_entities",
            },
        ]
        if brand_confidence_present:
            evidence.append(
                {
                    "check": "brand_confidence",
                    "value": round(brand_confidence, 2),
                    "source": "brand_disambiguation.exact_match_confidence",
                }
            )
        if kg_confidence_present:
            evidence.append(
                {
                    "check": "knowledge_graph_confidence",
                    "value": round(kg_confidence, 2),
                    "source": "knowledge_graph.confidence",
                }
            )

        weak_signals = 0
        if same_as_links < _MIN_SAME_AS_LINKS:
            weak_signals += 1
        if candidate_entities > 1:
            weak_signals += 1
        if brand_confidence_present and brand_confidence < _LOW_BRAND_CONFIDENCE_THRESHOLD:
            weak_signals += 1
        if kg_confidence_present and kg_confidence < _LOW_KG_CONFIDENCE_THRESHOLD:
            weak_signals += 1

        local = _local_section(payload) if is_local_brand else cast(Mapping[str, object], {})
        reputation = _reputation_section(payload) if is_local_brand else cast(Mapping[str, object], {})
        local_signals = self._local_signal_evidence(local, reputation)
        if is_local_brand:
            evidence.extend(local_signals["evidence"])
            weak_signals += local_signals["weak_signals"]

        if weak_signals == 0:
            return None

        return {
            "reason_code": ENTITY_CLARITY_WEAK,
            "evidence": evidence,
            "confidence": min(0.93, 0.4 + (weak_signals * 0.12)),
            "applicability": "all",
        }

    def _kg_presence_finding(self, payload: Mapping[str, object]) -> EntityFinding | None:
        brand = _brand_section(payload)
        knowledge_graph = _knowledge_graph_section(payload)
        wikidata = _wikidata_section(payload)
        if not brand and not knowledge_graph and not wikidata:
            return None

        kg_present, kg_minimal = _entity_presence_state(
            knowledge_graph,
            stable_keys=("id", "entity_id", "kgmid", "mid", "url"),
            presence_keys=("present", "has_presence", "detected"),
            confidence_keys=("confidence", "score", "confidence_score", "relevance_score"),
        )
        wikidata_present, wikidata_minimal = _entity_presence_state(
            wikidata,
            stable_keys=("qid", "id", "entity_id", "url"),
            presence_keys=("present", "has_entry", "detected"),
            confidence_keys=("confidence", "score"),
        )

        kg_missing = not kg_present or kg_minimal
        wikidata_missing = not wikidata_present or wikidata_minimal
        if not kg_missing and not wikidata_missing:
            return None

        evidence: list[FindingEvidence] = [
            {
                "check": "knowledge_graph_present",
                "value": kg_present,
                "source": "knowledge_graph.present",
            },
            {
                "check": "knowledge_graph_id",
                "value": _first_text(knowledge_graph, "id", "entity_id", "kgmid", "mid", "url"),
                "source": "knowledge_graph.id",
            },
            {
                "check": "wikidata_present",
                "value": wikidata_present,
                "source": "wikidata.present",
            },
            {
                "check": "wikidata_qid",
                "value": _first_text(wikidata, "qid", "id", "entity_id", "url"),
                "source": "wikidata.qid",
            },
        ]

        severity = int(kg_missing) + int(wikidata_missing)
        return {
            "reason_code": KG_PRESENCE_MISSING,
            "evidence": evidence,
            "confidence": min(0.92, 0.48 + (severity * 0.16)),
            "applicability": "all",
        }

    def _local_signal_evidence(
        self,
        local: Mapping[str, object],
        reputation: Mapping[str, object],
    ) -> LocalSignalSummary:
        evidence: list[FindingEvidence] = []
        weak_signals = 0

        if local:
            listing_count = _first_number(local, "listing_count", "local_listings", "citations", "directory_profiles")
            evidence.append(
                {
                    "check": "local_listing_count",
                    "value": int(listing_count),
                    "source": "local_presence.listing_count",
                }
            )
            if listing_count < _MIN_LOCAL_LISTINGS:
                weak_signals += 1

        if reputation:
            review_count_present = _has_any_key(reputation, "review_count", "reviews", "total_reviews")
            review_count = _first_number(reputation, "review_count", "reviews", "total_reviews")
            rating_present = _has_any_key(reputation, "average_rating", "rating", "review_rating")
            average_rating = _first_number(reputation, "average_rating", "rating", "review_rating")
            if review_count_present:
                evidence.append(
                    {
                        "check": "review_count",
                        "value": int(review_count),
                        "source": "reputation.review_count",
                    }
                )
                if review_count < _MIN_REVIEW_COUNT:
                    weak_signals += 1
            if rating_present:
                evidence.append(
                    {
                        "check": "average_rating",
                        "value": round(average_rating, 2),
                        "source": "reputation.average_rating",
                    }
                )
                if average_rating < _MIN_REVIEW_RATING:
                    weak_signals += 1

        return {"evidence": evidence, "weak_signals": weak_signals}


def _has_entity_context(payload: Mapping[str, object]) -> bool:
    return bool(_brand_section(payload) or _knowledge_graph_section(payload) or _wikidata_section(payload))


def _brand_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("brand_disambiguation", "brand", "entity", "identity"):
        section = _section(payload, key)
        if section:
            return section

    if _has_any_key(
        payload,
        "generic_brand",
        "is_generic_name",
        "is_generic_brand",
        "ambiguity_score",
        "disambiguation_difficulty",
        "genericity_score",
        "exact_match_confidence",
        "brand_confidence",
        "disambiguation_confidence",
        "candidate_entities",
        "candidates",
        "same_named_entities",
        "name_collisions",
        "similar_brand_count",
    ):
        return payload

    return {}


def _knowledge_graph_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("knowledge_graph", "kg", "google_knowledge_graph"):
        section = _section(payload, key)
        if section:
            return section

    if _has_any_key(
        payload,
        "kgmid",
        "mid",
        "knowledge_graph_present",
        "kg_confidence",
        "relevance_score",
        "has_presence",
    ):
        return payload

    return {}


def _wikidata_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("wikidata", "wikidata_entry"):
        section = _section(payload, key)
        if section:
            return section

    if _has_any_key(payload, "qid", "wikidata_present", "has_entry"):
        return payload

    return {}


def _local_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("local_presence", "local", "local_listings"):
        section = _section(payload, key)
        if section:
            return section

    if _has_any_key(payload, "listing_count", "local_listings", "citations", "directory_profiles"):
        return payload

    return {}


def _reputation_section(payload: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("reputation", "reviews", "review_signals"):
        section = _section(payload, key)
        if section:
            return section

    if _has_any_key(payload, "review_count", "reviews", "total_reviews", "average_rating", "rating"):
        return payload

    return {}


def _entity_presence_state(
    section: Mapping[str, object],
    *,
    stable_keys: tuple[str, ...],
    presence_keys: tuple[str, ...],
    confidence_keys: tuple[str, ...],
) -> tuple[bool, bool]:
    if not section:
        return False, True

    present = any(_as_bool(section.get(key)) for key in presence_keys if key in section)
    if not present and _first_text(section, *stable_keys):
        present = True
    if not present and _same_as_count(section) > 0:
        present = True

    if not present:
        return False, True

    stable_id = _first_text(section, *stable_keys)
    same_as_links = _same_as_count(section)
    confidence_present = _has_any_key(section, *confidence_keys)
    confidence = _first_number(section, *confidence_keys)
    minimal = (
        not stable_id
        and same_as_links == 0
        and (not confidence_present or confidence < _LOW_BRAND_CONFIDENCE_THRESHOLD)
    )
    return True, minimal


def _candidate_count(section: Mapping[str, object]) -> int:
    numeric_count = int(
        _first_number(section, "same_named_entities", "name_collisions", "similar_brand_count", "candidate_count")
    )
    list_count = 0
    for key in ("candidate_entities", "candidates", "matches", "entities"):
        list_count = max(list_count, len(_items_for_key(section, key)))
    return max(numeric_count, list_count)


def _same_as_count(*sections: Mapping[str, object]) -> int:
    count = 0
    for section in sections:
        if not section:
            continue
        for key in ("same_as", "sameAs", "same_as_links", "sameAsLinks"):
            count = max(count, _link_count(section.get(key)))
    return count


def _link_count(value: object) -> int:
    if isinstance(value, str):
        return 1 if value.strip() else 0
    if isinstance(value, Mapping):
        return len([item for item in value.values() if item])
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return len([item for item in value if item])
    return 0


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


def _first_text(item: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _first_number(item: Mapping[str, object], *keys: str) -> float:
    for key in keys:
        if key not in item:
            continue
        return _as_number(item.get(key))
    return 0.0


def _first_bool(item: Mapping[str, object], *keys: str) -> bool:
    for key in keys:
        if key not in item:
            continue
        return _as_bool(item.get(key))
    return False


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
