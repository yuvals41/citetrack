import subprocess
import sys
from pathlib import Path
from typing import cast

from pydantic import TypeAdapter

from ai_visibility.models import RunResult
from ai_visibility.recommendations import COMPETITOR_WINS, LOW_VISIBILITY, MISSING_CITATIONS
from ai_visibility.recommendations.engine import RecommendationsEngine


def _mock_run(
    workspace_slug: str,
    visibility_score: float,
    citation_coverage: float,
    competitor_wins: int,
    missing_citations: int,
) -> RunResult:
    payload: dict[str, object] = {
        "workspace_slug": workspace_slug,
        "visibility_score": visibility_score,
        "citation_coverage": citation_coverage,
        "competitor_wins": competitor_wins,
        "missing_citations": missing_citations,
        "prompt_category": ["awareness"],
    }
    return cast(RunResult, cast(object, payload))


def test_recommendations_engine_generates_recommendations_from_mock_run_data() -> None:
    engine = RecommendationsEngine()
    runs = [
        _mock_run("acme", visibility_score=0.2, citation_coverage=0.1, competitor_wins=2, missing_citations=4),
        _mock_run("acme", visibility_score=0.3, citation_coverage=0.2, competitor_wins=1, missing_citations=3),
    ]

    recommendations = engine.generate(workspace_slug="acme", runs=runs)
    rule_codes = {item.rule_code for item in recommendations}

    assert COMPETITOR_WINS in rule_codes
    assert MISSING_CITATIONS in rule_codes
    assert LOW_VISIBILITY in rule_codes


def test_recommendations_engine_empty_runs_returns_empty_list() -> None:
    recommendations = RecommendationsEngine().generate(workspace_slug="acme", runs=[])

    assert recommendations == []


def test_recommendations_are_scoped_to_workspace_slug() -> None:
    engine = RecommendationsEngine()
    runs = [_mock_run("irrelevant", 0.1, 0.1, 2, 2), _mock_run("irrelevant", 0.2, 0.2, 1, 2)]

    recommendations = engine.generate(workspace_slug="acme", runs=runs)

    assert recommendations
    assert all(item.workspace_slug == "acme" for item in recommendations)


def test_cli_recommend_latest_returns_json_with_recommendations_key() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "recommend-latest",
            "--workspace",
            "acme",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload_adapter: TypeAdapter[dict[str, object]] = TypeAdapter(dict[str, object])
    payload = payload_adapter.validate_json(result.stdout)
    assert ("recommendations" in payload) or ("degraded" in payload)


def test_cli_recommend_latest_accepts_disable_explanations_flag() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "recommend-latest",
            "--workspace",
            "acme",
            "--disable-explanations",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
