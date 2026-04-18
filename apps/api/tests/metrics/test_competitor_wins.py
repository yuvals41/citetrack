from ai_visibility.extraction.models import MentionResult
from ai_visibility.metrics.engine import MetricsEngine


def make_mention(
    *,
    brand_name: str,
    mentioned: bool,
    position: int | None,
) -> MentionResult:
    return MentionResult(
        brand_name=brand_name,
        mentioned=mentioned,
        sentiment="neutral",
        context_snippet="snippet" if mentioned else None,
        position_in_response=position,
    )


def test_competitor_wins_no_competitors_is_zero() -> None:
    engine = MetricsEngine()
    mentions = [make_mention(brand_name="Acme", mentioned=True, position=10)]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="Acme")

    assert snapshot.competitor_wins == 0


def test_competitor_before_primary_counts_win() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(brand_name="Acme", mentioned=True, position=10),
        make_mention(brand_name="Rival", mentioned=True, position=4),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="Acme")

    assert snapshot.competitor_wins == 1


def test_primary_before_competitor_is_not_a_win() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(brand_name="Acme", mentioned=True, position=3),
        make_mention(brand_name="Rival", mentioned=True, position=9),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="Acme")

    assert snapshot.competitor_wins == 0


def test_multiple_competitors_before_and_after_count_only_before_primary() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(brand_name="Acme", mentioned=True, position=10),
        make_mention(brand_name="RivalA", mentioned=True, position=2),
        make_mention(brand_name="RivalB", mentioned=True, position=8),
        make_mention(brand_name="RivalC", mentioned=True, position=15),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="Acme")

    assert snapshot.competitor_wins == 2


def test_primary_not_mentioned_counts_all_mentioned_competitors() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(brand_name="Acme", mentioned=False, position=None),
        make_mention(brand_name="RivalA", mentioned=True, position=1),
        make_mention(brand_name="RivalB", mentioned=True, position=6),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="Acme")

    assert snapshot.competitor_wins == 2


def test_empty_mentions_has_zero_competitor_wins() -> None:
    engine = MetricsEngine()

    snapshot = engine.compute("ws-1", "run-1", [], [], primary_brand="Acme")

    assert snapshot.competitor_wins == 0


def test_none_positions_are_excluded_from_competitor_wins() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(brand_name="Acme", mentioned=True, position=10),
        make_mention(brand_name="RivalA", mentioned=True, position=None),
        make_mention(brand_name="RivalB", mentioned=True, position=12),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="Acme")

    assert snapshot.competitor_wins == 0


def test_primary_brand_matching_is_case_insensitive() -> None:
    engine = MetricsEngine()
    mentions = [
        make_mention(brand_name="acme", mentioned=True, position=12),
        make_mention(brand_name="RIVAL", mentioned=True, position=4),
        make_mention(brand_name="Rival2", mentioned=True, position=20),
    ]

    snapshot = engine.compute("ws-1", "run-1", mentions, [], primary_brand="AcMe")

    assert snapshot.competitor_wins == 1
