# pyright: reportMissingImports=false

"""
Stateless scan executor for AI Visibility.

Pure function: ScanInput → ScanOutput.
NO database imports. NO Prisma. NO repositories.
"""

import time
from collections.abc import Callable

from loguru import logger

from ai_visibility.providers.gateway import LocationContext as GatewayLocationContext
from ai_visibility.runs.execution_core import (
    PipelineProgress,
    build_adapters,
    compute_pipeline_metrics,
    execute_scan_pipeline,
    run_async_in_thread,
)
from ai_visibility.runs.scan_strategy import ScanMode, get_strategy_for_mode
from ai_visibility.schema import LocationContext, MentionResult, ScanInput, ScanMetrics, ScanOutput, ScanProgress


def _to_gateway_location(loc: LocationContext) -> GatewayLocationContext:
    return GatewayLocationContext(
        city=loc.city,
        region=loc.region,
        country=loc.country_code,
    )


def _to_scan_progress(progress: PipelineProgress) -> ScanProgress:
    return ScanProgress(
        stage="scanning",
        provider=progress.provider,
        prompts_completed=progress.prompts_completed,
        prompts_total=progress.prompts_total,
        message=progress.message,
    )


async def execute_scan(
    scan_input: ScanInput,
    on_progress: Callable[[ScanProgress], None] | None = None,
) -> ScanOutput:
    start_time = time.time()
    job_id = getattr(scan_input, "job_id", "") or ""

    logger.info(
        f"[scan_executor/{job_id}] Starting scan: brand={scan_input.brand_name} "
        f"domain={scan_input.domain} providers={scan_input.providers}"
    )

    if on_progress is not None:
        on_progress(ScanProgress(stage="scanning", prompts_completed=0, prompts_total=0))

    strategy = get_strategy_for_mode(ScanMode.SCHEDULED)
    adapters = build_adapters(
        scan_input.providers,
        run_async_in_thread,
        strategy.strategy_version,
    )
    location = _to_gateway_location(scan_input.location)

    pipeline_result = await execute_scan_pipeline(
        providers=scan_input.providers,
        prompts=scan_input.prompts,
        max_prompts_per_provider=scan_input.max_prompts_per_provider,
        brand_names=[scan_input.brand_name],
        competitors=scan_input.competitors,
        location=location,
        strategy=strategy,
        adapters=adapters,
        workspace_slug="",
        on_progress=(lambda progress: on_progress(_to_scan_progress(progress))) if on_progress is not None else None,
    )

    if on_progress is not None:
        on_progress(
            ScanProgress(
                stage="extracting",
                prompts_completed=pipeline_result.prompts_completed,
                prompts_total=pipeline_result.total_prompts,
                message="Computing metrics...",
            )
        )

    successful_results = pipeline_result.successes
    metrics = compute_pipeline_metrics(successful_results)

    duration = time.time() - start_time

    if on_progress is not None:
        on_progress(
            ScanProgress(
                stage="complete",
                prompts_completed=pipeline_result.prompts_completed,
                prompts_total=pipeline_result.total_prompts,
                message=f"Scan complete in {duration:.1f}s",
            )
        )

    mentions = [
        MentionResult(
            provider=result.provider,
            model_name=result.adapter_result.model_name,
            prompt_id=result.prompt_id,
            prompt_text=result.prompt_text,
            raw_response=result.adapter_result.raw_response,
            brand_mentioned=result.brand_mentioned,
            brand_position=result.brand_position,
            sentiment=result.sentiment,
            sentiment_score=None,
            citations=[
                {"url": citation.url, "title": citation.title, "cited_text": citation.cited_text}
                for citation in result.normalized_citations
            ],
            reasoning=result.adapter_result.reasoning.strip() or None,
        )
        for result in successful_results
    ]

    provider_results = {
        provider: {
            "status": summary.status,
            "ok": summary.ok,
            "failed": summary.failed,
            "model": summary.model,
            **({"reason": summary.reason} if summary.reason is not None else {}),
        }
        for provider, summary in pipeline_result.provider_results.items()
    }

    output = ScanOutput(
        job_id=job_id,
        status="success" if mentions else "failed",
        duration=round(duration, 2),
        mentions=mentions,
        metrics=ScanMetrics(
            visibility_score=metrics.visibility_score,
            citation_coverage=metrics.citation_coverage,
            avg_position=metrics.avg_position,
            total_prompts=metrics.total_prompts,
            total_mentioned=metrics.total_mentioned,
            total_citations=metrics.total_citations,
        ),
        provider_results=provider_results,
    )

    logger.info(
        f"[scan_executor/{job_id}] Scan complete: {len(mentions)} mentions, "
        f"visibility={metrics.visibility_score:.2%}, duration={duration:.1f}s"
    )
    return output
