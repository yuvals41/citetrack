"""
Stateless scan executor for AI Visibility.

Pure function: ScanInput → ScanOutput.
NO database imports. NO Prisma. NO repositories.
This module is the core business logic extracted from RunOrchestrator,
designed to run in a stateless worker (RabbitMQ consumer or K8s job).
"""

import asyncio
import concurrent.futures
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from loguru import logger

from ai_visibility.extraction.models import CitationResult, MentionResult as ExtMentionResult
from ai_visibility.extraction.pipeline import ExtractionPipeline
from ai_visibility.providers import LLMConfig, ProviderError
from ai_visibility.providers.adapters import AdapterResult, GatewayScanAdapter, ScanAdapter
from ai_visibility.providers.adapters.google_ai_overview import GoogleAIOverviewAdapter
from ai_visibility.providers.gateway import LocationContext as GatewayLocationContext, ProviderGateway
from ai_visibility.prompts.renderer import PromptRenderError, PromptRenderer
from ai_visibility.runs.scan_strategy import ProviderConfig, ScanMode, get_strategy_for_mode
from ai_visibility.schema import (
    LocationContext,
    MentionResult,
    PromptDefinition,
    ScanInput,
    ScanMetrics,
    ScanOutput,
    ScanProgress,
)

T = TypeVar("T")


def _run_async_in_thread(coro: Coroutine[object, object, T]) -> T:
    """Run an async coroutine from a sync context, handling nested event loops."""
    try:
        _ = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        return asyncio.run(coro)


def _to_gateway_location(loc: LocationContext) -> GatewayLocationContext:
    """Convert schema LocationContext to gateway LocationContext."""
    return GatewayLocationContext(
        city=loc.city,
        region=loc.region,
        country=loc.country_code,
    )


def _resolve_provider_key(provider: str) -> str:
    """Map provider name to strategy key (e.g. openai → chatgpt)."""
    aliases = {"openai": "chatgpt"}
    return aliases.get(provider, provider)


def _build_adapters(
    providers: list[str],
    run_async: Callable[[Coroutine[object, object, Any]], Any],
    strategy_version: str,
) -> dict[str, ScanAdapter]:
    """Build adapter instances for requested providers. NO DB dependency."""
    adapters: dict[str, ScanAdapter] = {}

    for provider in providers:
        provider_key = _resolve_provider_key(provider)

        if provider_key == "google_ai_overview":
            adapters[provider_key] = GoogleAIOverviewAdapter()
            continue

        if provider_key == "google_ai_mode_serpapi":
            try:
                from ai_visibility.providers.adapters.google_ai_mode_serpapi import (
                    GoogleAIModeSerpAPIAdapter,
                )

                adapters[provider_key] = GoogleAIModeSerpAPIAdapter()
            except Exception:
                logger.warning(f"[scan_executor] Could not load google_ai_mode_serpapi adapter")
            continue

        # For all other providers, use GatewayScanAdapter
        gateway = ProviderGateway(config=LLMConfig(provider=provider))
        adapter = GatewayScanAdapter(
            gateway,
            run_async,
            strategy_version=strategy_version,
        )
        adapters[provider_key] = adapter
        # Also register under original name if different
        if provider_key != provider:
            adapters[provider] = adapter

    return adapters


def _inject_location_prompt(
    prompt_text: str,
    provider_key: str,
    location: GatewayLocationContext,
) -> str:
    """Append location suffix for providers that need it in the prompt."""
    if provider_key not in {"gemini", "grok", "google_ai_overview"} or not location.is_set:
        return prompt_text
    return f"{prompt_text}{location.to_prompt_suffix()}"


async def execute_scan(
    scan_input: ScanInput,
    on_progress: Callable[[ScanProgress], None] | None = None,
) -> ScanOutput:
    """
    Execute a full AI Visibility scan. Stateless — no DB, no Prisma.

    Args:
        scan_input: Fully self-contained scan configuration.
        on_progress: Optional callback for progress updates.

    Returns:
        ScanOutput with mentions, metrics, and provider results.
    """
    start_time = time.time()
    job_id = scan_input.job_id or ""

    logger.info(
        f"[scan_executor/{job_id}] Starting scan: brand={scan_input.brand_name} "
        f"domain={scan_input.domain} providers={scan_input.providers}"
    )

    if on_progress:
        on_progress(ScanProgress(stage="scanning", prompts_completed=0, prompts_total=0))

    # Build strategy and adapters
    strategy = get_strategy_for_mode(ScanMode.SCHEDULED)
    adapters = _build_adapters(
        scan_input.providers,
        _run_async_in_thread,
        strategy.strategy_version,
    )

    location = _to_gateway_location(scan_input.location)
    renderer = PromptRenderer()
    brand_names = [scan_input.brand_name]
    extractor = ExtractionPipeline(brand_names=brand_names)
    semaphore = asyncio.Semaphore(3)

    # Compute total prompts across all providers
    total_prompts_count = 0
    for provider in scan_input.providers:
        provider_key = _resolve_provider_key(provider)
        provider_config = strategy.providers.get(provider_key)
        if provider_config is None:
            continue
        max_prompts = min(scan_input.max_prompts_per_provider, provider_config.max_prompts)
        total_prompts_count += min(len(scan_input.prompts), max_prompts)

    if on_progress:
        on_progress(
            ScanProgress(
                stage="scanning",
                prompts_completed=0,
                prompts_total=total_prompts_count,
            )
        )

    # Execute prompts across all providers
    all_mentions: list[MentionResult] = []
    all_ext_mentions: list[ExtMentionResult] = []
    all_ext_citations: list[CitationResult] = []
    provider_results: dict[str, dict[str, Any]] = {}
    prompts_completed = 0

    for provider in scan_input.providers:
        provider_key = _resolve_provider_key(provider)
        provider_config = strategy.providers.get(provider_key)
        if provider_config is None:
            logger.warning(f"[scan_executor/{job_id}] No strategy config for provider: {provider}")
            provider_results[provider] = {"status": "skipped", "reason": "no_strategy_config"}
            continue

        adapter = adapters.get(provider_key) or adapters.get(provider)
        if adapter is None:
            logger.warning(f"[scan_executor/{job_id}] No adapter for provider: {provider}")
            provider_results[provider] = {"status": "skipped", "reason": "no_adapter"}
            continue

        max_prompts = min(scan_input.max_prompts_per_provider, provider_config.max_prompts)
        prompts_to_run = scan_input.prompts[:max_prompts]

        if on_progress:
            on_progress(
                ScanProgress(
                    stage="scanning",
                    provider=provider,
                    prompts_completed=prompts_completed,
                    prompts_total=total_prompts_count,
                    message=f"Scanning {provider}...",
                )
            )

        provider_mention_results = await _execute_provider_prompts(
            provider=provider,
            provider_key=provider_key,
            provider_config=provider_config,
            adapter=adapter,
            prompts=prompts_to_run,
            brand_names=brand_names,
            competitors=scan_input.competitors,
            location=location,
            renderer=renderer,
            extractor=extractor,
            semaphore=semaphore,
            job_id=job_id,
        )

        # Collect results
        provider_ok = 0
        provider_failed = 0
        for result in provider_mention_results:
            if result.get("ok"):
                provider_ok += 1
                mention = result["mention"]
                all_mentions.append(mention)
                all_ext_mentions.extend(result.get("ext_mentions", []))
                all_ext_citations.extend(result.get("ext_citations", []))
            else:
                provider_failed += 1

            prompts_completed += 1
            if on_progress:
                on_progress(
                    ScanProgress(
                        stage="scanning",
                        provider=provider,
                        prompts_completed=prompts_completed,
                        prompts_total=total_prompts_count,
                    )
                )

        provider_results[provider] = {
            "status": "completed" if provider_failed == 0 else "partial",
            "ok": provider_ok,
            "failed": provider_failed,
            "model": provider_config.model_name,
        }

    # Compute metrics
    if on_progress:
        on_progress(
            ScanProgress(
                stage="extracting",
                prompts_completed=prompts_completed,
                prompts_total=total_prompts_count,
                message="Computing metrics...",
            )
        )

    metrics = _compute_scan_metrics(
        mentions=all_mentions,
        ext_mentions=all_ext_mentions,
        ext_citations=all_ext_citations,
        brand_name=scan_input.brand_name,
        job_id=job_id,
    )

    duration = time.time() - start_time

    if on_progress:
        on_progress(
            ScanProgress(
                stage="complete",
                prompts_completed=prompts_completed,
                prompts_total=total_prompts_count,
                message=f"Scan complete in {duration:.1f}s",
            )
        )

    has_mentions = len(all_mentions) > 0
    status = "success" if has_mentions else "failed"

    output = ScanOutput(
        job_id=job_id,
        status=status,
        duration=round(duration, 2),
        mentions=all_mentions,
        metrics=metrics,
        provider_results=provider_results,
    )

    logger.info(
        f"[scan_executor/{job_id}] Scan complete: {len(all_mentions)} mentions, "
        f"visibility={metrics.visibility_score:.2%}, duration={duration:.1f}s"
    )
    return output


async def _execute_provider_prompts(
    *,
    provider: str,
    provider_key: str,
    provider_config: ProviderConfig,
    adapter: ScanAdapter,
    prompts: list[PromptDefinition],
    brand_names: list[str],
    competitors: list[str],
    location: GatewayLocationContext,
    renderer: PromptRenderer,
    extractor: ExtractionPipeline,
    semaphore: asyncio.Semaphore,
    job_id: str,
) -> list[dict[str, Any]]:
    """Execute all prompts for a single provider with Semaphore(3) parallelism."""

    async def _run_single(idx: int, prompt_def: PromptDefinition) -> dict[str, Any]:
        async with semaphore:
            try:
                # Render prompt with brand/competitor substitution
                competitor_name = competitors[idx % len(competitors)] if competitors else "competitors"
                rendered = renderer.render(
                    prompt_def.template,
                    brand=brand_names[0],
                    competitor=competitor_name,
                )
                rendered_with_location = _inject_location_prompt(rendered, provider_key, location)

                # Execute via adapter (sync call, adapters handle async internally)
                adapter_result = adapter.execute(
                    rendered_with_location,
                    "",  # workspace_slug not needed for stateless execution
                    provider_config,
                    location,
                )
                validated = AdapterResult.model_validate(adapter_result)

                # Extract mentions and citations
                parser_result = extractor.extract(validated.raw_response)
                ext_mentions = list(parser_result.mentions)
                ext_citations = list(parser_result.citations)

                # Build fallback mention if parser fell back
                if parser_result.parser_status == "fallback":
                    ext_mentions.append(
                        ExtMentionResult(
                            brand_name=brand_names[0],
                            mentioned=False,
                            position_in_response=None,
                            context_snippet=None,
                        )
                    )

                # Determine if brand was mentioned
                brand_mentioned = any(m.mentioned for m in ext_mentions)
                brand_position = None
                sentiment_value = None
                sentiment_score = None
                for m in ext_mentions:
                    if m.mentioned and m.position_in_response is not None:
                        brand_position = m.position_in_response
                        break
                for m in ext_mentions:
                    if m.sentiment and m.sentiment != "unknown":
                        sentiment_value = m.sentiment
                        break

                # Build citations list
                citations_list = []
                for c in ext_citations:
                    if c.url and c.status == "found":
                        citations_list.append({"url": c.url, "domain": c.domain})
                # Also include adapter-level citations
                for c in validated.citations:
                    url = c.get("url")
                    if isinstance(url, str) and url.strip():
                        citations_list.append({"url": url.strip()})

                mention = MentionResult(
                    provider=provider,
                    model_name=validated.model_name,
                    prompt_id=prompt_def.id,
                    prompt_text=rendered_with_location,
                    raw_response=validated.raw_response,
                    brand_mentioned=brand_mentioned,
                    brand_position=brand_position,
                    sentiment=sentiment_value,
                    sentiment_score=sentiment_score,
                    citations=citations_list,
                    reasoning=validated.reasoning if validated.reasoning.strip() else None,
                )

                return {
                    "ok": True,
                    "mention": mention,
                    "ext_mentions": ext_mentions,
                    "ext_citations": ext_citations,
                }

            except (ProviderError, ValueError, TypeError, PromptRenderError) as exc:
                logger.warning(f"[scan_executor/{job_id}] Prompt failed for {provider}: {type(exc).__name__}: {exc}")
                return {"ok": False, "error": str(exc), "provider": provider}
            except Exception as exc:
                logger.error(f"[scan_executor/{job_id}] Unexpected error for {provider}: {type(exc).__name__}: {exc}")
                return {"ok": False, "error": str(exc), "provider": provider}

    tasks = [_run_single(idx, prompt_def) for idx, prompt_def in enumerate(prompts)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    normalized: list[dict[str, Any]] = []
    for result in results:
        if isinstance(result, BaseException):
            normalized.append({"ok": False, "error": str(result), "provider": provider})
        else:
            normalized.append(result)

    return normalized


def _compute_scan_metrics(
    *,
    mentions: list[MentionResult],
    ext_mentions: list[ExtMentionResult],
    ext_citations: list[CitationResult],
    brand_name: str,
    job_id: str,
) -> ScanMetrics:
    total_prompts = len(mentions)
    total_mentioned = sum(1 for m in mentions if m.brand_mentioned)
    total_citations = sum(len(m.citations) for m in mentions)

    # Use MetricsEngine for visibility/citation scores
    visibility_score = total_mentioned / total_prompts if total_prompts > 0 else 0.0
    citation_coverage = 0.0
    if ext_citations:
        found = sum(1 for c in ext_citations if c.status == "found")
        citation_coverage = found / len(ext_citations) if ext_citations else 0.0

    # Average position (lower is better)
    positions = [m.brand_position for m in mentions if m.brand_mentioned and m.brand_position is not None]
    avg_position = sum(positions) / len(positions) if positions else 0.0

    return ScanMetrics(
        visibility_score=round(visibility_score, 4),
        citation_coverage=round(citation_coverage, 4),
        avg_position=round(avg_position, 2),
        total_prompts=total_prompts,
        total_mentioned=total_mentioned,
        total_citations=total_citations,
    )
