from typing import Literal

from ai_visibility.extraction.models import CitationResult, MentionResult
from ai_visibility.metrics.engine import FORMULA_VERSION, MetricSnapshot, MetricsEngine


def make_mention(*, mentioned: bool, position: int | None = None) -> MentionResult:
    return MentionResult(
        brand_name="Solara",
        mentioned=mentioned,
        sentiment="neutral",
        context_snippet="ctx" if mentioned else None,
        position_in_response=position,
    )


def make_citation(status: Literal["found", "no_citation"]) -> CitationResult:
    return CitationResult(status=status)


def make_snapshot(
    *,
    run_id: str,
    visibility_score: float,
    citation_coverage: float,
    competitor_wins: int,
    prompt_version: str | None,
) -> MetricSnapshot:
    return MetricSnapshot(
        workspace_id="ws_1",
        run_id=run_id,
        visibility_score=visibility_score,
        citation_coverage=citation_coverage,
        competitor_wins=competitor_wins,
        total_prompts=10,
        mentioned_count=5,
        prompt_version=prompt_version,
        model="gpt-4.1",
    )


def test_compute_empty_mentions_yields_zero_visibility_score() -> None:
    engine = MetricsEngine()

    snapshot = engine.compute("ws_1", "run_1", [], [])

    assert snapshot.visibility_score == 0.0


def test_compute_empty_citations_yields_zero_citation_coverage() -> None:
    engine = MetricsEngine()

    snapshot = engine.compute("ws_1", "run_1", [make_mention(mentioned=True, position=1)], [])

    assert snapshot.citation_coverage == 0.0


def test_compute_all_mentions_true_yields_visibility_one() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True, position=1), make_mention(mentioned=True, position=2)]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.visibility_score == 1.0
    assert snapshot.mentioned_count == 2


def test_compute_all_mentions_false_yields_visibility_zero() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=False), make_mention(mentioned=False)]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.visibility_score == 0.0
    assert snapshot.mentioned_count == 0


def test_compute_mixed_mentions_yields_expected_ratio() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(mentioned=True, position=1),
        make_mention(mentioned=True, position=4),
        make_mention(mentioned=False),
        make_mention(mentioned=False),
        make_mention(mentioned=True, position=2),
    ]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.visibility_score == 0.6


def test_compute_competitor_wins_position_one_not_counted() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True, position=1)]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.competitor_wins == 0


def test_compute_competitor_wins_position_greater_than_one_counted() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True, position=3), make_mention(mentioned=True, position=10)]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.competitor_wins == 2


def test_compute_competitor_wins_position_none_not_counted() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(mentioned=True, position=None), make_mention(mentioned=False, position=None)]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.competitor_wins == 0


def test_compute_citation_coverage_all_found_is_one() -> None:
    engine = MetricsEngine()
    citations = [make_citation("found"), make_citation("found"), make_citation("found")]

    snapshot = engine.compute("ws_1", "run_1", [], citations)

    assert snapshot.citation_coverage == 1.0


def test_compute_citation_coverage_all_no_citation_is_zero() -> None:
    engine = MetricsEngine()
    citations = [make_citation("no_citation"), make_citation("no_citation")]

    snapshot = engine.compute("ws_1", "run_1", [], citations)

    assert snapshot.citation_coverage == 0.0


def test_compute_citation_coverage_mixed_ratio_is_correct() -> None:
    engine = MetricsEngine()
    citations = [
        make_citation("found"),
        make_citation("no_citation"),
        make_citation("found"),
        make_citation("no_citation"),
    ]

    snapshot = engine.compute("ws_1", "run_1", [], citations)

    assert snapshot.citation_coverage == 0.5


def test_compare_same_prompt_version_returns_ok_with_deltas() -> None:
    engine = MetricsEngine()
    older = make_snapshot(
        run_id="run_old",
        visibility_score=0.4,
        citation_coverage=0.3,
        competitor_wins=4,
        prompt_version="v1",
    )
    newer = make_snapshot(
        run_id="run_new",
        visibility_score=0.9,
        citation_coverage=0.8,
        competitor_wins=1,
        prompt_version="v1",
    )

    result = engine.compare(older, newer)

    assert result.comparison_status == "ok"
    assert result.delta_visibility_score == 0.5
    assert result.delta_citation_coverage == 0.5
    assert result.delta_competitor_wins == -3


def test_compare_different_prompt_version_returns_mismatch_label() -> None:
    engine = MetricsEngine()
    left = make_snapshot(
        run_id="run_a",
        visibility_score=0.6,
        citation_coverage=0.4,
        competitor_wins=2,
        prompt_version="v1",
    )
    right = make_snapshot(
        run_id="run_b",
        visibility_score=0.7,
        citation_coverage=0.6,
        competitor_wins=1,
        prompt_version="v2",
    )

    result = engine.compare(left, right)

    assert result.comparison_status == "version_mismatch"
    assert result.note is not None
    assert "prompt_version mismatch" in result.note


def test_trend_delta_positive_change() -> None:
    engine = MetricsEngine()
    previous = make_snapshot(
        run_id="run_prev",
        visibility_score=0.2,
        citation_coverage=0.2,
        competitor_wins=3,
        prompt_version="v1",
    )
    current = make_snapshot(
        run_id="run_curr",
        visibility_score=0.9,
        citation_coverage=0.8,
        competitor_wins=1,
        prompt_version="v1",
    )

    assert engine.trend_delta(current, previous) == 0.7


def test_trend_delta_negative_change() -> None:
    engine = MetricsEngine()
    previous = make_snapshot(
        run_id="run_prev",
        visibility_score=0.8,
        citation_coverage=0.8,
        competitor_wins=1,
        prompt_version="v1",
    )
    current = make_snapshot(
        run_id="run_curr",
        visibility_score=0.3,
        citation_coverage=0.4,
        competitor_wins=2,
        prompt_version="v1",
    )

    assert engine.trend_delta(current, previous) == -0.5


def test_trend_delta_no_change_is_zero() -> None:
    engine = MetricsEngine()
    previous = make_snapshot(
        run_id="run_prev",
        visibility_score=0.55,
        citation_coverage=0.5,
        competitor_wins=2,
        prompt_version="v1",
    )
    current = make_snapshot(
        run_id="run_curr",
        visibility_score=0.55,
        citation_coverage=0.7,
        competitor_wins=2,
        prompt_version="v1",
    )

    assert engine.trend_delta(current, previous) == 0.0


def test_compute_total_prompts_matches_mentions_length() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(mentioned=True, position=1),
        make_mention(mentioned=False),
        make_mention(mentioned=True, position=5),
        make_mention(mentioned=False),
    ]

    snapshot = engine.compute("ws_1", "run_1", mentions, [])

    assert snapshot.total_prompts == 4


def test_compute_populates_formula_version_field() -> None:
    engine = MetricsEngine()

    snapshot = engine.compute("ws_1", "run_1", [make_mention(mentioned=True, position=1)], [])

    assert snapshot.formula_version == FORMULA_VERSION
