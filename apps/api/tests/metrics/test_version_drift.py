from ai_visibility.metrics import MetricsEngine, MetricSnapshot


def make_snapshot(*, run_id: str, prompt_version: str | None) -> MetricSnapshot:
    return MetricSnapshot(
        workspace_id="ws-1",
        run_id=run_id,
        visibility_score=0.5,
        citation_coverage=0.5,
        competitor_wins=0,
        total_prompts=2,
        mentioned_count=1,
        prompt_version=prompt_version,
    )


def test_incompatible_versions_labeled() -> None:
    engine = MetricsEngine()
    run_a = make_snapshot(run_id="run-a", prompt_version="v1")
    run_b = make_snapshot(run_id="run-b", prompt_version="v2")

    result = engine.compare(run_a, run_b)

    assert result.comparison_status == "version_mismatch"


def test_compatible_versions_ok() -> None:
    engine = MetricsEngine()
    run_a = make_snapshot(run_id="run-a", prompt_version="v1")
    run_b = make_snapshot(run_id="run-b", prompt_version="v1")

    result = engine.compare(run_a, run_b)

    assert result.comparison_status == "ok"
