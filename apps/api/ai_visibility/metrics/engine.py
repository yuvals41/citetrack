from typing import Literal

from pydantic import BaseModel

from ai_visibility.extraction.models import CitationResult, MentionResult

FORMULA_VERSION = "1.0.0"


class MetricSnapshot(BaseModel):
    workspace_id: str
    run_id: str
    formula_version: str = FORMULA_VERSION
    visibility_score: float
    citation_coverage: float
    competitor_wins: int
    total_prompts: int
    mentioned_count: int
    prompt_version: str | None = None
    model: str | None = None


class ComparisonResult(BaseModel):
    run_a_id: str
    run_b_id: str
    comparison_status: Literal["ok", "version_mismatch"]
    delta_visibility_score: float | None = None
    delta_citation_coverage: float | None = None
    delta_competitor_wins: int | None = None
    note: str | None = None


class TrendPoint(BaseModel):
    run_id: str
    workspace_id: str
    formula_version: str
    prompt_version: str | None = None
    model: str | None = None
    visibility_score: float
    citation_coverage: float
    competitor_wins: int
    total_prompts: int
    mentioned_count: int
    comparison_status: Literal["ok", "version_mismatch"] = "ok"
    delta_visibility_score: float | None = None
    delta_citation_coverage: float | None = None
    delta_competitor_wins: int | None = None


class TrendSeries(BaseModel):
    formula_version: str
    prompt_version: str | None = None
    model: str | None = None
    comparison_status: Literal["ok", "version_mismatch"]
    points: list[TrendPoint]


class TrendEngine:
    def __init__(self, metrics_engine: "MetricsEngine") -> None:
        self._metrics_engine: MetricsEngine = metrics_engine

    def build_trend_series(self, snapshots: list[MetricSnapshot]) -> list[TrendSeries]:
        if not snapshots:
            return []

        grouped_snapshots: dict[tuple[str, str | None, str | None], list[MetricSnapshot]] = {}
        group_order: list[tuple[str, str | None, str | None]] = []
        for snapshot in snapshots:
            key = self._version_key(snapshot)
            if key not in grouped_snapshots:
                grouped_snapshots[key] = []
                group_order.append(key)
            grouped_snapshots[key].append(snapshot)

        has_multiple_groups = len(grouped_snapshots) > 1
        trend_series: list[TrendSeries] = []

        for key in group_order:
            grouped = grouped_snapshots[key]
            is_compatible_group = len(grouped) > 1
            group_status: Literal["ok", "version_mismatch"]
            if is_compatible_group or not has_multiple_groups:
                group_status = "ok"
            else:
                group_status = "version_mismatch"

            points: list[TrendPoint] = []
            previous_snapshot: MetricSnapshot | None = None
            for snapshot in grouped:
                point = TrendPoint(
                    run_id=snapshot.run_id,
                    workspace_id=snapshot.workspace_id,
                    formula_version=snapshot.formula_version,
                    prompt_version=snapshot.prompt_version,
                    model=snapshot.model,
                    visibility_score=snapshot.visibility_score,
                    citation_coverage=snapshot.citation_coverage,
                    competitor_wins=snapshot.competitor_wins,
                    total_prompts=snapshot.total_prompts,
                    mentioned_count=snapshot.mentioned_count,
                    comparison_status=group_status,
                )

                if previous_snapshot is not None and is_compatible_group:
                    comparison = self._metrics_engine.compare(previous_snapshot, snapshot)
                    if comparison.comparison_status == "ok":
                        point.delta_visibility_score = comparison.delta_visibility_score
                        point.delta_citation_coverage = comparison.delta_citation_coverage
                        point.delta_competitor_wins = comparison.delta_competitor_wins

                previous_snapshot = snapshot
                points.append(point)

            trend_series.append(
                TrendSeries(
                    formula_version=key[0],
                    prompt_version=key[1],
                    model=key[2],
                    comparison_status=group_status,
                    points=points,
                )
            )

        return trend_series

    def _version_key(self, snapshot: MetricSnapshot) -> tuple[str, str | None, str | None]:
        return (snapshot.formula_version, snapshot.prompt_version, snapshot.model)


class MetricsEngine:
    def compute(
        self,
        workspace_id: str,
        run_id: str,
        mentions: list[MentionResult],
        citations: list[CitationResult],
        primary_brand: str = "",
        prompt_version: str | None = None,
        model: str | None = None,
    ) -> MetricSnapshot:
        total = len(mentions)
        mentioned_count = sum(1 for mention in mentions if mention.mentioned)
        visibility_score = mentioned_count / total if total > 0 else 0.0

        found_citations = [citation for citation in citations if citation.status == "found"]
        total_citations = len(citations)
        citation_coverage = len(found_citations) / total_citations if total_citations > 0 else 0.0

        if primary_brand:
            primary_brand_lower = primary_brand.lower()
            primary_positions = [
                mention.position_in_response
                for mention in mentions
                if mention.brand_name
                and mention.brand_name.lower() == primary_brand_lower
                and mention.mentioned
                and mention.position_in_response is not None
            ]
            competitor_positions = [
                mention.position_in_response
                for mention in mentions
                if mention.brand_name
                and mention.brand_name.lower() != primary_brand_lower
                and mention.mentioned
                and mention.position_in_response is not None
            ]

            if not competitor_positions:
                competitor_wins = 0
            else:
                min_primary = min(primary_positions) if primary_positions else float("inf")
                competitor_wins = sum(1 for position in competitor_positions if position < min_primary)
        else:
            competitor_wins = sum(
                1
                for mention in mentions
                if mention.mentioned and mention.position_in_response is not None and mention.position_in_response > 1
            )

        return MetricSnapshot(
            workspace_id=workspace_id,
            run_id=run_id,
            visibility_score=round(visibility_score, 4),
            citation_coverage=round(citation_coverage, 4),
            competitor_wins=competitor_wins,
            total_prompts=total,
            mentioned_count=mentioned_count,
            prompt_version=prompt_version,
            model=model,
        )

    def compare(self, snapshot_a: MetricSnapshot, snapshot_b: MetricSnapshot) -> ComparisonResult:
        mismatches: list[str] = []
        if snapshot_a.formula_version != snapshot_b.formula_version:
            mismatches.append(
                f"formula_version mismatch: {snapshot_a.formula_version!r} vs {snapshot_b.formula_version!r}"
            )
        if snapshot_a.prompt_version != snapshot_b.prompt_version:
            mismatches.append(
                f"prompt_version mismatch: {snapshot_a.prompt_version!r} vs {snapshot_b.prompt_version!r}"
            )
        if snapshot_a.model != snapshot_b.model:
            mismatches.append(f"model mismatch: {snapshot_a.model!r} vs {snapshot_b.model!r}")

        if mismatches:
            return ComparisonResult(
                run_a_id=snapshot_a.run_id,
                run_b_id=snapshot_b.run_id,
                comparison_status="version_mismatch",
                note="; ".join(mismatches),
            )

        return ComparisonResult(
            run_a_id=snapshot_a.run_id,
            run_b_id=snapshot_b.run_id,
            comparison_status="ok",
            delta_visibility_score=round(snapshot_b.visibility_score - snapshot_a.visibility_score, 4),
            delta_citation_coverage=round(snapshot_b.citation_coverage - snapshot_a.citation_coverage, 4),
            delta_competitor_wins=snapshot_b.competitor_wins - snapshot_a.competitor_wins,
        )

    def trend_delta(self, current: MetricSnapshot, previous: MetricSnapshot) -> float:
        return round(current.visibility_score - previous.visibility_score, 4)

    def build_trend_series(self, snapshots: list[MetricSnapshot]) -> list[TrendSeries]:
        return TrendEngine(metrics_engine=self).build_trend_series(snapshots)
