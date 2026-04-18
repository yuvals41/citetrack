from collections.abc import Sequence
from typing import cast

from ai_visibility.models import RunResult
from ai_visibility.recommendations.engine import (
    COMPETITOR_WINS,
    LOW_VISIBILITY,
    MISSING_CITATIONS,
    PROMPT_CATEGORY_GAP,
    RecommendationsEngine,
)


def _run(
    *,
    visibility_score: float | None = 0.6,
    competitor_wins: int | None = 0,
    missing_citations: int | None = 0,
    citation_coverage: float | None = 1.0,
    prompt_category: object = "awareness",
) -> RunResult:
    payload: dict[str, object | None] = {
        "visibility_score": visibility_score,
        "competitor_wins": competitor_wins,
        "missing_citations": missing_citations,
        "citation_coverage": citation_coverage,
        "prompt_category": prompt_category,
    }
    return cast(RunResult, cast(object, payload))


def _codes(recommendations: Sequence[object]) -> set[str]:
    return {cast(str, getattr(rec, "rule_code")) for rec in recommendations}


def test_empty_runs_returns_empty_recommendations() -> None:
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=[])
    assert recommendations == []


def test_single_run_never_triggers_competitor_wins_rule() -> None:
    runs = [
        _run(
            visibility_score=0.2,
            competitor_wins=5,
            missing_citations=2,
            citation_coverage=0.25,
            prompt_category="awareness",
        )
    ]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    codes = _codes(recommendations)
    assert COMPETITOR_WINS not in codes
    assert LOW_VISIBILITY in codes
    assert MISSING_CITATIONS in codes
    assert PROMPT_CATEGORY_GAP in codes


def test_all_perfect_scores_return_no_recommendations() -> None:
    runs = [
        _run(
            visibility_score=1.0,
            competitor_wins=0,
            missing_citations=0,
            citation_coverage=1.0,
            prompt_category=["awareness", "consideration", "decision"],
        ),
        _run(
            visibility_score=1.0,
            competitor_wins=0,
            missing_citations=0,
            citation_coverage=1.0,
            prompt_category=["buying_intent", "comparison", "recommendation", "informational"],
        ),
    ]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert recommendations == []


def test_low_visibility_triggers_when_average_below_threshold() -> None:
    runs = [_run(visibility_score=0.1), _run(visibility_score=0.39)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    low = [rec for rec in recommendations if rec.rule_code == LOW_VISIBILITY]
    assert len(low) == 1
    assert low[0].priority == "high"


def test_low_visibility_does_not_trigger_at_or_above_threshold() -> None:
    runs = [_run(visibility_score=0.5), _run(visibility_score=0.4)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert LOW_VISIBILITY not in _codes(recommendations)


def test_low_visibility_boundary_exactly_point_four_does_not_trigger() -> None:
    runs = [_run(visibility_score=0.2), _run(visibility_score=0.6)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert LOW_VISIBILITY not in _codes(recommendations)


def test_competitor_wins_triggers_on_two_or_more_runs() -> None:
    runs = [_run(competitor_wins=1), _run(competitor_wins=2), _run(competitor_wins=0)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    competitor = [rec for rec in recommendations if rec.rule_code == COMPETITOR_WINS]
    assert len(competitor) == 1
    assert competitor[0].priority == "high"


def test_competitor_wins_does_not_trigger_for_single_winning_run() -> None:
    runs = [_run(competitor_wins=0), _run(competitor_wins=1)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert COMPETITOR_WINS not in _codes(recommendations)


def test_missing_citations_triggers_for_any_missing_citations() -> None:
    runs = [_run(missing_citations=1, citation_coverage=0.9)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    missing = [rec for rec in recommendations if rec.rule_code == MISSING_CITATIONS]
    assert len(missing) == 1
    assert missing[0].priority == "medium"


def test_missing_citations_triggers_for_low_coverage_even_without_missing_count() -> None:
    runs = [_run(missing_citations=0, citation_coverage=0.2)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert MISSING_CITATIONS in _codes(recommendations)


def test_prompt_category_gap_triggers_when_required_categories_missing() -> None:
    runs = [_run(prompt_category="buying_intent"), _run(prompt_category=["comparison"])]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    gap = [rec for rec in recommendations if rec.rule_code == PROMPT_CATEGORY_GAP]
    assert len(gap) == 1
    assert gap[0].priority == "low"
    assert "recommendation" in gap[0].description.lower() or "informational" in gap[0].description.lower()


def test_prompt_category_gap_does_not_trigger_when_all_required_categories_present() -> None:
    runs = [
        _run(prompt_category=["buying_intent", "comparison"]),
        _run(prompt_category=["recommendation", "informational"]),
    ]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert PROMPT_CATEGORY_GAP not in _codes(recommendations)


def test_workspace_slug_is_applied_to_all_recommendations() -> None:
    runs = [_run(visibility_score=0.1), _run(visibility_score=0.2)]
    recommendations = RecommendationsEngine().generate(workspace_slug="scope-slug", runs=runs)

    assert recommendations
    assert all(rec.workspace_slug == "scope-slug" for rec in recommendations)


def test_priority_ordering_is_high_then_medium_then_low_for_matching_case() -> None:
    runs = [
        _run(visibility_score=0.1, missing_citations=2, citation_coverage=0.1, prompt_category="buying_intent"),
        _run(visibility_score=0.2, missing_citations=0, citation_coverage=0.8, prompt_category="buying_intent"),
    ]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    priorities = [rec.priority for rec in recommendations]
    assert priorities == ["medium", "high", "low"] or priorities == ["high", "medium", "low"]
    assert "high" in priorities and "medium" in priorities and "low" in priorities


def test_recommendation_shape_contains_required_fields() -> None:
    runs = [_run(visibility_score=0.1), _run(visibility_score=0.2)]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert recommendations
    for recommendation in recommendations:
        dumped = recommendation.model_dump()
        assert set(dumped.keys()) == {"rule_code", "title", "description", "priority", "workspace_slug"}
        assert isinstance(dumped["rule_code"], str)
        assert isinstance(dumped["title"], str)
        assert isinstance(dumped["description"], str)
        assert dumped["priority"] in {"high", "medium", "low"}
        assert dumped["workspace_slug"] == "ws-a"


def test_multiple_rules_trigger_simultaneously_returns_all() -> None:
    runs = [
        _run(
            visibility_score=0.1,
            competitor_wins=1,
            missing_citations=1,
            citation_coverage=0.2,
            prompt_category="awareness",
        ),
        _run(
            visibility_score=0.2,
            competitor_wins=1,
            missing_citations=0,
            citation_coverage=1.0,
            prompt_category="consideration",
        ),
    ]
    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=runs)

    assert _codes(recommendations) == {
        COMPETITOR_WINS,
        MISSING_CITATIONS,
        LOW_VISIBILITY,
        PROMPT_CATEGORY_GAP,
    }


def test_runs_with_none_and_missing_values_do_not_crash() -> None:
    sparse_run = cast(
        RunResult,
        cast(
            object,
            {
                "visibility_score": None,
                "competitor_wins": None,
                "missing_citations": None,
                "citation_coverage": None,
                "prompt_category": None,
            },
        ),
    )
    weird_run = cast(
        RunResult,
        cast(
            object,
            {
                "visibility_score": "not-a-number",
                "competitor_wins": False,
                "missing_citations": "x",
                "citation_coverage": "y",
                "prompt_category": [None, "awareness", 123],
            },
        ),
    )

    recommendations = RecommendationsEngine().generate(workspace_slug="ws-a", runs=[sparse_run, weird_run])
    assert isinstance(recommendations, list)
