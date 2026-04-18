from ai_visibility.metrics.engine import FORMULA_VERSION, MetricsEngine, MetricSnapshot


def _snapshot(
    *,
    run_id: str,
    visibility_score: float,
    formula_version: str = FORMULA_VERSION,
    prompt_version: str | None = "v1",
    model: str | None = "gpt-4.1",
) -> MetricSnapshot:
    return MetricSnapshot(
        workspace_id="ws-1",
        run_id=run_id,
        formula_version=formula_version,
        visibility_score=visibility_score,
        citation_coverage=0.4,
        competitor_wins=1,
        total_prompts=10,
        mentioned_count=4,
        prompt_version=prompt_version,
        model=model,
    )


def test_build_trend_series_empty_returns_empty() -> None:
    engine = MetricsEngine()

    assert engine.build_trend_series([]) == []


def test_build_trend_series_groups_compatible_and_separates_mismatches() -> None:
    engine = MetricsEngine()
    snapshots = [
        _snapshot(run_id="run-1", visibility_score=0.3),
        _snapshot(run_id="run-2", visibility_score=0.6),
        _snapshot(run_id="run-3", visibility_score=0.7, formula_version="2.0.0"),
        _snapshot(run_id="run-4", visibility_score=0.8, prompt_version="v2"),
        _snapshot(run_id="run-5", visibility_score=0.9, model="claude-sonnet-4"),
    ]

    result = engine.build_trend_series(snapshots)

    assert len(result) == 4

    compatible_series = next(series for series in result if len(series.points) == 2)
    assert compatible_series.formula_version == FORMULA_VERSION
    assert compatible_series.prompt_version == "v1"
    assert compatible_series.model == "gpt-4.1"
    assert compatible_series.comparison_status == "ok"
    assert compatible_series.points[0].comparison_status == "ok"
    assert compatible_series.points[1].comparison_status == "ok"
    assert compatible_series.points[1].delta_visibility_score == 0.3

    mismatch_series = [series for series in result if series.comparison_status == "version_mismatch"]
    assert len(mismatch_series) == 3

    mismatch_keys = {(series.formula_version, series.prompt_version, series.model) for series in mismatch_series}
    assert ("2.0.0", "v1", "gpt-4.1") in mismatch_keys
    assert (FORMULA_VERSION, "v2", "gpt-4.1") in mismatch_keys
    assert (FORMULA_VERSION, "v1", "claude-sonnet-4") in mismatch_keys


def test_compare_formula_version_mismatch_is_labeled() -> None:
    engine = MetricsEngine()
    left = _snapshot(run_id="run-left", visibility_score=0.5, formula_version="1.0.0")
    right = _snapshot(run_id="run-right", visibility_score=0.6, formula_version="2.0.0")

    result = engine.compare(left, right)

    assert result.comparison_status == "version_mismatch"
    assert result.note is not None
    assert "formula_version mismatch" in result.note


def test_compare_prompt_version_mismatch_is_labeled() -> None:
    engine = MetricsEngine()
    left = _snapshot(run_id="run-left", visibility_score=0.5, prompt_version="v1")
    right = _snapshot(run_id="run-right", visibility_score=0.6, prompt_version="v2")

    result = engine.compare(left, right)

    assert result.comparison_status == "version_mismatch"
    assert result.note is not None
    assert "prompt_version mismatch" in result.note


def test_compare_model_mismatch_is_labeled() -> None:
    engine = MetricsEngine()
    left = _snapshot(run_id="run-left", visibility_score=0.5, model="gpt-4.1")
    right = _snapshot(run_id="run-right", visibility_score=0.6, model="claude-sonnet-4")

    result = engine.compare(left, right)

    assert result.comparison_status == "version_mismatch"
    assert result.note is not None
    assert "model mismatch" in result.note
