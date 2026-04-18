from typing import Literal

from ai_visibility.extraction.models import CitationResult, MentionResult
from ai_visibility.metrics import MetricsEngine, MetricSnapshot


def make_mention(*, mentioned: bool, position: int | None = None) -> MentionResult:
    return MentionResult(
        brand_name="Acme",
        mentioned=mentioned,
        position_in_response=position,
    )


def make_citation(status: Literal["found", "no_citation"]) -> CitationResult:
    return CitationResult(status=status)


def make_snapshot(
    *,
    run_id: str,
    visibility_score: float,
    citation_coverage: float = 0.0,
    competitor_wins: int = 0,
    prompt_version: str | None = "v1",
) -> MetricSnapshot:
    return MetricSnapshot(
        workspace_id="ws-1",
        run_id=run_id,
        visibility_score=visibility_score,
        citation_coverage=citation_coverage,
        competitor_wins=competitor_wins,
        total_prompts=1,
        mentioned_count=1,
        prompt_version=prompt_version,
    )


def test_visibility_score_all_mentioned() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True) for _ in range(3)]

    snapshot = engine.compute("ws-1", "run-1", mentions, [])

    assert snapshot.visibility_score == 1.0


def test_visibility_score_none_mentioned() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=False) for _ in range(3)]

    snapshot = engine.compute("ws-1", "run-1", mentions, [])

    assert snapshot.visibility_score == 0.0


def test_visibility_score_partial() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(mentioned=True),
        make_mention(mentioned=True),
        make_mention(mentioned=False),
        make_mention(mentioned=False),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [])

    assert snapshot.visibility_score == 0.5


def test_competitor_wins_brand_ahead() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True, position=1)]

    snapshot = engine.compute("ws-1", "run-1", mentions, [])

    assert snapshot.competitor_wins == 0


def test_competitor_wins_competitor_ahead() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True, position=3)]

    snapshot = engine.compute("ws-1", "run-1", mentions, [])

    assert snapshot.competitor_wins == 1


def test_citation_coverage_all_found() -> None:
    engine = MetricsEngine()
    citations = [make_citation("found") for _ in range(3)]

    snapshot = engine.compute("ws-1", "run-1", [], citations)

    assert snapshot.citation_coverage == 1.0


def test_citation_coverage_none_found() -> None:
    engine = MetricsEngine()
    citations = [make_citation("no_citation") for _ in range(3)]

    snapshot = engine.compute("ws-1", "run-1", [], citations)

    assert snapshot.citation_coverage == 0.0


def test_formula_version_present() -> None:
    assert "formula_version" in MetricSnapshot.model_fields


def test_version_mismatch_label() -> None:
    engine = MetricsEngine()
    older = make_snapshot(run_id="run-a", visibility_score=0.4, prompt_version="v1")
    newer = make_snapshot(run_id="run-b", visibility_score=0.7, prompt_version="v2")

    result = engine.compare(older, newer)

    assert result.comparison_status == "version_mismatch"


def test_trend_delta_positive() -> None:
    engine = MetricsEngine()
    current = make_snapshot(run_id="run-current", visibility_score=0.8)
    previous = make_snapshot(run_id="run-previous", visibility_score=0.5)

    result = engine.trend_delta(current, previous)

    assert result == 0.3


def test_trend_delta_negative() -> None:
    engine = MetricsEngine()
    current = make_snapshot(run_id="run-current", visibility_score=0.3)
    previous = make_snapshot(run_id="run-previous", visibility_score=0.7)

    result = engine.trend_delta(current, previous)

    assert result == -0.4
