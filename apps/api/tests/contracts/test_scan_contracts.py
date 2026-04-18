import json
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from ai_visibility.contracts import (
    Observation,
    RecommendationItem,
    ScanJob,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8")))


def test_scan_job_contract() -> None:
    payload = _fixture("scan_job.json")

    result = ScanJob.model_validate(payload)

    assert result.id == payload["id"]
    assert result.workspace_slug == payload["workspace_slug"]
    assert result.strategy_version == payload["strategy_version"]


def test_observation_contract() -> None:
    payload = _fixture("observation.json")

    result = Observation.model_validate(payload)

    assert result.brand_mentioned is True
    assert result.response_excerpt == payload["response_excerpt"]


def test_recommendation_item_contract() -> None:
    payload = _fixture("recommendation_item.json")

    result = RecommendationItem.model_validate(payload)

    assert result.code == payload["code"]
    assert result.reason == payload["reason"]
    assert result.evidence_refs == payload["evidence_refs"]
    assert result.impact == payload["impact"]
    assert result.next_step == payload["next_step"]
    assert result.confidence == payload["confidence"]


def test_missing_version_metadata() -> None:
    payload = _fixture("recommendation_item_missing_rule_version.json")

    with pytest.raises(ValidationError):
        _ = RecommendationItem.model_validate(payload)
