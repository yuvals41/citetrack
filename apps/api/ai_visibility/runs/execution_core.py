# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Callable, Coroutine, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar

from loguru import logger

from ai_visibility.extraction.models import CitationResult
from ai_visibility.extraction.models import MentionResult as ExtractedMentionResult
from ai_visibility.extraction.pipeline import ExtractionPipeline
from ai_visibility.prompts.renderer import PromptRenderer, PromptRenderError
from ai_visibility.providers import LLMConfig, ProviderError
from ai_visibility.providers.adapters import AdapterResult, GatewayScanAdapter, ScanAdapter
from ai_visibility.providers.adapters.google_ai_overview import GoogleAIOverviewAdapter
from ai_visibility.providers.gateway import LocationContext, ProviderGateway, ProviderResponse
from ai_visibility.runs.scan_strategy import ProviderConfig, ScanStrategy
from ai_visibility.schema import PromptDefinition

T = TypeVar("T")


@dataclass(slots=True)
class PipelinePrompt:
    id: str
    template: str
    version: str = "1.0.0"


@dataclass(slots=True)
class CitationCandidate:
    url: str
    title: str
    cited_text: str | None = None


@dataclass(slots=True)
class PromptExecutionSuccess:
    provider: str
    provider_key: str
    prompt_id: str
    prompt_text: str
    adapter_result: AdapterResult
    mention_results: list[ExtractedMentionResult]
    citation_results: list[CitationResult]
    normalized_citations: list[CitationCandidate]
    parser_version: str
    brand_mentioned: bool
    brand_position: int | None
    sentiment: str | None


@dataclass(slots=True)
class PromptExecutionFailure:
    provider: str
    prompt_id: str
    error_message: str
    error_type: str


@dataclass(slots=True)
class ProviderExecutionSummary:
    status: str
    ok: int
    failed: int
    model: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class PipelineProgress:
    provider: str | None
    prompts_completed: int
    prompts_total: int
    message: str | None = None


@dataclass(slots=True)
class PipelineMetrics:
    visibility_score: float
    citation_coverage: float
    avg_position: float
    total_prompts: int
    total_mentioned: int
    total_citations: int


@dataclass(slots=True)
class ScanPipelineResult:
    results: list[PromptExecutionSuccess | PromptExecutionFailure]
    provider_results: dict[str, ProviderExecutionSummary]
    prompts_completed: int
    total_prompts: int

    @property
    def successes(self) -> list[PromptExecutionSuccess]:
        return [result for result in self.results if isinstance(result, PromptExecutionSuccess)]

    @property
    def failures(self) -> list[PromptExecutionFailure]:
        return [result for result in self.results if isinstance(result, PromptExecutionFailure)]


def run_async_in_thread(coro: Coroutine[object, object, T]) -> T:
    """Run an async coroutine from a sync context, handling nested event loops."""
    try:
        _ = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        return asyncio.run(coro)


def resolve_provider_key(provider: str) -> str:
    aliases = {"openai": "chatgpt"}
    return aliases.get(provider, provider)


def build_adapters(
    providers: Sequence[str],
    run_async: Callable[[Coroutine[object, object, ProviderResponse]], ProviderResponse],
    strategy_version: str,
) -> dict[str, ScanAdapter]:
    adapters: dict[str, ScanAdapter] = {}

    for provider in providers:
        provider_key = resolve_provider_key(provider)

        if provider_key == "google_ai_overview":
            adapters[provider_key] = GoogleAIOverviewAdapter()
            continue

        if provider_key == "google_ai_mode_serpapi":
            try:
                from ai_visibility.providers.adapters.google_ai_mode_serpapi import GoogleAIModeSerpAPIAdapter

                adapters[provider_key] = GoogleAIModeSerpAPIAdapter()
            except Exception:
                logger.warning("[execution_core] Could not load google_ai_mode_serpapi adapter")
            continue

        gateway = ProviderGateway(config=LLMConfig(provider=provider))
        adapter = GatewayScanAdapter(
            gateway,
            run_async,
            strategy_version=strategy_version,
        )
        adapters[provider_key] = adapter
        if provider_key != provider:
            adapters[provider] = adapter

    return adapters


def normalize_prompts(
    prompts: Sequence[PipelinePrompt | PromptDefinition | Mapping[str, object]],
) -> list[PipelinePrompt]:
    normalized: list[PipelinePrompt] = []
    for idx, prompt in enumerate(prompts):
        if isinstance(prompt, PipelinePrompt):
            normalized.append(prompt)
            continue
        if isinstance(prompt, PromptDefinition):
            normalized.append(
                PipelinePrompt(
                    id=prompt.id,
                    template=prompt.template,
                    version=prompt.version,
                )
            )
            continue

        prompt_id = str(prompt.get("id", f"prompt-{idx + 1}"))
        template = str(prompt.get("template", ""))
        version = str(prompt.get("version", "1.0.0"))
        normalized.append(PipelinePrompt(id=prompt_id, template=template, version=version))

    return normalized


def inject_location_prompt(prompt_text: str, provider_key: str, location: LocationContext) -> str:
    if provider_key not in {"gemini", "grok", "google_ai_overview"} or not location.is_set:
        return prompt_text
    return f"{prompt_text}{location.to_prompt_suffix()}"


def build_citation_candidates(
    adapter_result: AdapterResult,
    extracted_citations: Sequence[CitationResult],
) -> list[CitationCandidate]:
    candidates: list[CitationCandidate] = []
    for citation in adapter_result.citations:
        url_value = citation.get("url")
        if not isinstance(url_value, str) or not url_value.strip():
            continue
        url = url_value.strip()
        title_value = citation.get("title") or citation.get("text")
        title = str(title_value).strip() if title_value is not None else url
        cited_text_value = citation.get("text")
        cited_text = (
            str(cited_text_value).strip()
            if isinstance(cited_text_value, str) and cited_text_value.strip()
            else None
        )
        candidates.append(CitationCandidate(url=url, title=title or url, cited_text=cited_text))

    for citation in extracted_citations:
        if citation.url is None or not citation.url.strip():
            continue
        url = citation.url.strip()
        title = (citation.domain or url).strip()
        candidates.append(CitationCandidate(url=url, title=title, cited_text=None))

    deduped: dict[tuple[str, str, str | None], CitationCandidate] = {}
    for candidate in candidates:
        deduped[(candidate.url, candidate.title, candidate.cited_text)] = candidate
    return list(deduped.values())


def compute_pipeline_metrics(results: Sequence[PromptExecutionSuccess]) -> PipelineMetrics:
    total_prompts = len(results)
    total_mentioned = sum(1 for result in results if result.brand_mentioned)
    total_citations = sum(len(result.normalized_citations) for result in results)
    visibility_score = total_mentioned / total_prompts if total_prompts > 0 else 0.0

    extracted_citations = [citation for result in results for citation in result.citation_results]
    citation_coverage = 0.0
    if extracted_citations:
        found = sum(1 for citation in extracted_citations if citation.status == "found")
        citation_coverage = found / len(extracted_citations)

    positions = [
        result.brand_position
        for result in results
        if result.brand_mentioned and result.brand_position is not None
    ]
    avg_position = sum(positions) / len(positions) if positions else 0.0

    return PipelineMetrics(
        visibility_score=round(visibility_score, 4),
        citation_coverage=round(citation_coverage, 4),
        avg_position=round(avg_position, 2),
        total_prompts=total_prompts,
        total_mentioned=total_mentioned,
        total_citations=total_citations,
    )


async def execute_scan_pipeline(
    *,
    providers: Sequence[str],
    prompts: Sequence[PipelinePrompt | PromptDefinition | Mapping[str, object]],
    max_prompts_per_provider: int,
    brand_names: Sequence[str],
    competitors: Sequence[str],
    location: LocationContext,
    strategy: ScanStrategy,
    adapters: Mapping[str, ScanAdapter],
    workspace_slug: str,
    prompt_renderer: PromptRenderer | None = None,
    extractor: ExtractionPipeline | None = None,
    concurrency_limit: int = 3,
    on_progress: Callable[[PipelineProgress], None] | None = None,
) -> ScanPipelineResult:
    normalized_prompts = normalize_prompts(prompts)
    prompt_renderer = prompt_renderer or PromptRenderer()
    extractor = extractor or ExtractionPipeline(brand_names=list(brand_names))
    semaphore = asyncio.Semaphore(concurrency_limit)

    total_prompts = 0
    for provider in providers:
        provider_key = resolve_provider_key(provider)
        provider_config = strategy.providers.get(provider_key)
        if provider_config is None:
            continue
        max_prompts = min(max_prompts_per_provider, provider_config.max_prompts)
        total_prompts += min(len(normalized_prompts), max_prompts)

    results: list[PromptExecutionSuccess | PromptExecutionFailure] = []
    provider_results: dict[str, ProviderExecutionSummary] = {}
    prompts_completed = 0

    for provider in providers:
        provider_key = resolve_provider_key(provider)
        provider_config = strategy.providers.get(provider_key)
        if provider_config is None:
            logger.warning(f"[execution_core] No strategy config for provider: {provider}")
            provider_results[provider] = ProviderExecutionSummary(
                status="skipped",
                ok=0,
                failed=0,
                reason="no_strategy_config",
            )
            continue

        adapter = adapters.get(provider_key) or adapters.get(provider)
        if adapter is None:
            logger.warning(f"[execution_core] No adapter for provider: {provider}")
            provider_results[provider] = ProviderExecutionSummary(
                status="skipped",
                ok=0,
                failed=0,
                model=provider_config.model_name,
                reason="no_adapter",
            )
            continue

        max_prompts = min(max_prompts_per_provider, provider_config.max_prompts)
        prompts_to_run = normalized_prompts[:max_prompts]

        if on_progress is not None:
            on_progress(
                PipelineProgress(
                    provider=provider,
                    prompts_completed=prompts_completed,
                    prompts_total=total_prompts,
                    message=f"Scanning {provider}...",
                )
            )

        provider_run_results = await _execute_provider_prompts(
            provider=provider,
            provider_key=provider_key,
            provider_config=provider_config,
            adapter=adapter,
            prompts=prompts_to_run,
            brand_names=list(brand_names),
            competitors=list(competitors),
            location=location,
            renderer=prompt_renderer,
            extractor=extractor,
            semaphore=semaphore,
            workspace_slug=workspace_slug,
        )

        provider_ok = 0
        provider_failed = 0
        for provider_result in provider_run_results:
            if isinstance(provider_result, PromptExecutionSuccess):
                provider_ok += 1
            else:
                provider_failed += 1
            results.append(provider_result)
            prompts_completed += 1

            if on_progress is not None:
                on_progress(
                    PipelineProgress(
                        provider=provider,
                        prompts_completed=prompts_completed,
                        prompts_total=total_prompts,
                    )
                )

        provider_results[provider] = ProviderExecutionSummary(
            status="completed" if provider_failed == 0 else "partial",
            ok=provider_ok,
            failed=provider_failed,
            model=provider_config.model_name,
        )

    return ScanPipelineResult(
        results=results,
        provider_results=provider_results,
        prompts_completed=prompts_completed,
        total_prompts=total_prompts,
    )


async def _execute_provider_prompts(
    *,
    provider: str,
    provider_key: str,
    provider_config: ProviderConfig,
    adapter: ScanAdapter,
    prompts: Sequence[PipelinePrompt],
    brand_names: Sequence[str],
    competitors: Sequence[str],
    location: LocationContext,
    renderer: PromptRenderer,
    extractor: ExtractionPipeline,
    semaphore: asyncio.Semaphore,
    workspace_slug: str,
) -> list[PromptExecutionSuccess | PromptExecutionFailure]:
    async def _run_single(idx: int, prompt_def: PipelinePrompt) -> PromptExecutionSuccess | PromptExecutionFailure:
        async with semaphore:
            try:
                competitor_name = competitors[idx % len(competitors)] if competitors else "competitors"
                rendered = renderer.render(
                    prompt_def.template,
                    brand=brand_names[0],
                    competitor=competitor_name,
                )
                rendered_with_location = inject_location_prompt(rendered, provider_key, location)

                adapter_result = adapter.execute(
                    rendered_with_location,
                    workspace_slug,
                    provider_config,
                    location,
                )
                validated = AdapterResult.model_validate(adapter_result)

                parser_result = extractor.extract(validated.raw_response)
                mention_results = list(parser_result.mentions)
                citation_results = list(parser_result.citations)

                if parser_result.parser_status == "fallback":
                    mention_results.append(
                        ExtractedMentionResult(
                            brand_name=brand_names[0],
                            mentioned=False,
                            position_in_response=None,
                            context_snippet=None,
                        )
                    )

                brand_mentioned = any(result.mentioned for result in mention_results)
                brand_position = next(
                    (
                        result.position_in_response
                        for result in mention_results
                        if result.mentioned and result.position_in_response is not None
                    ),
                    None,
                )
                sentiment = next(
                    (
                        result.sentiment
                        for result in mention_results
                        if result.sentiment and result.sentiment != "unknown"
                    ),
                    None,
                )

                return PromptExecutionSuccess(
                    provider=provider,
                    provider_key=provider_key,
                    prompt_id=prompt_def.id,
                    prompt_text=rendered_with_location,
                    adapter_result=validated,
                    mention_results=mention_results,
                    citation_results=citation_results,
                    normalized_citations=build_citation_candidates(validated, citation_results),
                    parser_version=parser_result.parser_version,
                    brand_mentioned=brand_mentioned,
                    brand_position=brand_position,
                    sentiment=sentiment,
                )
            except (ProviderError, ValueError, TypeError, PromptRenderError) as exc:
                logger.warning(f"[execution_core] Prompt failed for {provider}: {type(exc).__name__}: {exc}")
                return PromptExecutionFailure(
                    provider=provider,
                    prompt_id=prompt_def.id,
                    error_message=str(exc),
                    error_type=type(exc).__name__,
                )
            except Exception as exc:
                logger.error(f"[execution_core] Unexpected error for {provider}: {type(exc).__name__}: {exc}")
                return PromptExecutionFailure(
                    provider=provider,
                    prompt_id=prompt_def.id,
                    error_message=str(exc),
                    error_type=type(exc).__name__,
                )

    tasks = [_run_single(idx, prompt_def) for idx, prompt_def in enumerate(prompts)]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    normalized_results: list[PromptExecutionSuccess | PromptExecutionFailure] = []
    for idx, result in enumerate(raw_results):
        if isinstance(result, BaseException):
            normalized_results.append(
                PromptExecutionFailure(
                    provider=provider,
                    prompt_id=prompts[idx].id,
                    error_message=str(result),
                    error_type=type(result).__name__,
                )
            )
            continue
        normalized_results.append(result)

    return normalized_results
