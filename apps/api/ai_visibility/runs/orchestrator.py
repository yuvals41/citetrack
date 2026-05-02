# pyright: reportMissingImports=false

import asyncio
import hashlib
import uuid
from collections.abc import Coroutine
from datetime import datetime, timezone
from typing import Literal, TypeVar, cast

from loguru import logger
from pydantic import BaseModel, Field

from ai_visibility.contracts.scan_contracts import LifecycleStatus
from ai_visibility.extraction.models import CitationResult, MentionResult
from ai_visibility.metrics.engine import MetricsEngine, MetricSnapshot
from ai_visibility.prompts import DEFAULT_PROMPTS
from ai_visibility.prompts.library import PromptLibrary
from ai_visibility.prompts.renderer import PromptRenderer
from ai_visibility.providers import LLMConfig, ProviderGateway
from ai_visibility.providers.adapters import AdapterResult, GatewayScanAdapter, ScanAdapter
from ai_visibility.providers.adapters.google_ai_overview import GoogleAIOverviewAdapter
from ai_visibility.providers.gateway import LocationContext
from ai_visibility.runs.execution_core import (
    PipelinePrompt,
    PromptExecutionFailure,
    PromptExecutionSuccess,
    execute_scan_pipeline,
    normalize_prompts,
    resolve_provider_key,
    run_async_in_thread,
)
from ai_visibility.runs.scan_strategy import ProviderConfig, ScanMode, ScanStrategy, get_strategy_for_mode
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories import (
    MentionRepository,
    MetricRepository,
    RunRepository,
    ScanEvidenceRepository,
    WorkspaceRepository,
)
from ai_visibility.storage.types import (
    MentionRecord,
    MetricSnapshotRecord,
    ObservationRecord,
    PromptExecutionCitationRecord,
    PromptExecutionRecord,
    RunRecord,
    ScanExecutionRecord,
    ScanJobRecord,
    WorkspaceRecord,
)

T = TypeVar("T")
REASONING_SEPARATOR = "\n\n[AI_REASONING]\n"


class ScanResult(BaseModel):
    run_id: str
    workspace_slug: str
    status: Literal[
        "queued",
        "running",
        "completed_with_partial_failures",
        "failed",
        "completed",
        "dry_run",
    ]
    results_count: int = 0
    provider: str = "openai"
    model: str | None = None
    prompt_version: str = "1.0.0"
    started_at: str
    completed_at: str | None = None
    failed_providers: list[str] = Field(default_factory=list)
    error_message: str | None = None


class RunOrchestrator:
    _inflight_scans: dict[tuple[str, str, str | None], asyncio.Task[ScanResult]] = {}
    _brand_names_resolved: bool
    workspace_slug: str
    provider: str
    model: str | None
    brand_names: list[str]
    prompt_library: PromptLibrary
    prompt_renderer: PromptRenderer
    gateway: ProviderGateway
    adapters: dict[str, ScanAdapter]
    strategy: ScanStrategy
    metrics_engine: MetricsEngine

    def __init__(
        self,
        workspace_slug: str,
        provider: str = "openai",
        model: str | None = None,
        brand_names: list[str] | None = None,
        adapters: dict[str, ScanAdapter] | None = None,
    ):
        self.workspace_slug = workspace_slug
        self.provider = provider
        self.model = model
        self.brand_names = brand_names or []
        self._brand_names_resolved = bool(brand_names)
        self.strategy = get_strategy_for_mode(ScanMode.SCHEDULED)
        self.prompt_library = PromptLibrary(prompts=DEFAULT_PROMPTS)
        self.prompt_renderer = PromptRenderer()
        self.gateway = ProviderGateway(config=LLMConfig(provider=provider, model=model))
        self.metrics_engine = MetricsEngine()
        default_adapter = GatewayScanAdapter(
            self.gateway,
            self._run_async,
            strategy_version=self.strategy.strategy_version,
        )
        self.adapters = adapters or {
            self._resolve_strategy_provider(provider): default_adapter,
            provider: default_adapter,
            "google_ai_overview": GoogleAIOverviewAdapter(),
        }

    def _run_async(self, coro: Coroutine[object, object, T]) -> T:
        return run_async_in_thread(coro)

    async def scan(self, dry_run: bool = False) -> ScanResult:
        if dry_run:
            return await self._scan_once(dry_run=True)

        scan_key = (self.workspace_slug, self.provider, self.model)
        inflight_scan = self._inflight_scans.get(scan_key)
        if inflight_scan is not None:
            return await asyncio.shield(inflight_scan)

        inflight_scan = asyncio.create_task(self._scan_once(dry_run=False))
        self._inflight_scans[scan_key] = inflight_scan
        try:
            return await asyncio.shield(inflight_scan)
        finally:
            if self._inflight_scans.get(scan_key) is inflight_scan:
                _ = self._inflight_scans.pop(scan_key, None)

    async def _scan_once(self, dry_run: bool = False) -> ScanResult:
        if dry_run:
            run_id = str(uuid.uuid4())
            started_at = datetime.now(timezone.utc).isoformat()
            return ScanResult(
                run_id=run_id,
                workspace_slug=self.workspace_slug,
                status="dry_run",
                provider=self.provider,
                model=self.model,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        context = await self._prepare_scan_context()
        results = await self._execute_prompts(context)
        evidence = self._build_evidence(results, context)
        metrics = self._compute_metrics(results, context)
        persisted = await self._persist(context, evidence, metrics, results)
        status = cast(
            Literal[
                "queued",
                "running",
                "completed_with_partial_failures",
                "failed",
                "completed",
                "dry_run",
            ],
            persisted["status"],
        )
        return ScanResult(
            run_id=cast(str, context["run_id"]),
            workspace_slug=self.workspace_slug,
            status=status,
            results_count=cast(int, persisted["results_count"]),
            provider=cast(str, persisted["provider_name"]),
            model=cast(str | None, persisted["model_name"]),
            started_at=cast(str, context["started_at"]),
            completed_at=cast(str, persisted["completed_at"]),
            failed_providers=cast(list[str], persisted["failed_providers"]),
            error_message=cast(str | None, persisted["last_error_message"]),
        )

    async def _prepare_scan_context(self) -> dict[str, object]:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()

        prisma = await get_prisma()
        workspace_repo = WorkspaceRepository(prisma)
        ws = await workspace_repo.get_by_slug(self.workspace_slug)
        workspace_id = ws["id"] if ws else self.workspace_slug
        if not self._brand_names_resolved and ws:
            brand = ws.get("brand_name") or self.workspace_slug
            self.brand_names = [brand]
        if not self.brand_names:
            self.brand_names = [self.workspace_slug]

        location_context = self._build_location_context(ws)
        provider_key = self._resolve_strategy_provider(self.provider)
        provider_config = self.strategy.providers.get(provider_key)
        if provider_config is None:
            raise ValueError(f"No provider config found for: {self.provider}")
        adapter = self.adapters.get(provider_key) or self.adapters.get(self.provider)
        if adapter is None:
            raise ValueError(f"No scan adapter registered for provider: {self.provider}")

        competitor_names = await self._load_competitor_names(workspace_id)
        prompts = normalize_prompts(self.prompt_library.list_prompts())
        prompt_version = prompts[0].version if prompts else "1.0.0"
        max_prompts = min(3, provider_config.max_prompts)

        scan_job_idempotency_key = self._idempotency_key(
            "scan_job",
            run_id,
            self.workspace_slug,
            self.strategy.strategy_version,
            prompt_version,
            self.strategy.scan_mode.value,
        )
        scan_job_id = self._stable_id("scan_job", scan_job_idempotency_key)

        scan_execution_idempotency_key = self._idempotency_key(
            "scan_execution",
            run_id,
            scan_job_id,
            provider_key,
            provider_config.model_name,
            provider_config.model_name,
        )
        scan_execution_id = self._stable_id("scan_execution", scan_execution_idempotency_key)

        return {
            "run_id": run_id,
            "started_at": started_at,
            "prisma": prisma,
            "workspace_id": workspace_id,
            "location_context": location_context,
            "provider_key": provider_key,
            "provider_config": provider_config,
            "adapter": adapter,
            "competitor_names": competitor_names,
            "prompts": prompts,
            "prompt_version": prompt_version,
            "max_prompts": max_prompts,
            "scan_job_id": scan_job_id,
            "scan_job_idempotency_key": scan_job_idempotency_key,
            "scan_execution_id": scan_execution_id,
            "scan_execution_idempotency_key": scan_execution_idempotency_key,
        }

    async def _execute_prompts(
        self,
        context: dict[str, object],
    ) -> list[PromptExecutionSuccess | PromptExecutionFailure]:
        provider_key = cast(str, context["provider_key"])
        adapter = cast(ScanAdapter, context["adapter"])
        location_context = cast(LocationContext, context["location_context"])
        competitor_names = cast(list[str], context["competitor_names"])
        prompts = cast(list[PipelinePrompt], context["prompts"])
        max_prompts = cast(int, context["max_prompts"])

        pipeline_result = await execute_scan_pipeline(
            providers=[self.provider],
            prompts=prompts,
            max_prompts_per_provider=max_prompts,
            brand_names=self.brand_names,
            competitors=competitor_names,
            location=location_context,
            strategy=self.strategy,
            adapters={provider_key: adapter, self.provider: adapter},
            workspace_slug=self.workspace_slug,
            prompt_renderer=self.prompt_renderer,
        )
        return pipeline_result.results

    def _build_evidence(
        self,
        results: list[PromptExecutionSuccess | PromptExecutionFailure],
        context: dict[str, object],
    ) -> dict[str, object]:
        workspace_id = cast(str, context["workspace_id"])
        run_id = cast(str, context["run_id"])
        scan_execution_id = cast(str, context["scan_execution_id"])

        results_count = 0
        failed_prompts = 0
        last_error_message: str | None = None
        adapter_results: list[AdapterResult] = []
        all_mention_results: list[MentionResult] = []
        all_citation_results: list[CitationResult] = []
        all_mentions: list[MentionRecord] = []
        prompt_execution_payloads: list[
            tuple[PromptExecutionRecord, list[ObservationRecord], list[PromptExecutionCitationRecord]]
        ] = []

        for result in results:
            if isinstance(result, PromptExecutionFailure):
                failed_prompts += 1
                last_error_message = result.error_message
                logger.warning(f"Prompt execution failed: {result.error_type}: {result.error_message}")
                continue

            results_count += 1
            adapter_results.append(result.adapter_result)
            all_mention_results.extend(result.mention_results)
            all_citation_results.extend(result.citation_results)

            prompt_execution_key = self._idempotency_key(
                "prompt_execution",
                scan_execution_id,
                result.prompt_id,
                result.adapter_result.provider,
                self._content_hash(result.prompt_text),
                self._content_hash(result.adapter_result.raw_response),
            )
            prompt_execution_id = self._stable_id("prompt_execution", prompt_execution_key)
            prompt_execution_record: PromptExecutionRecord = {
                "id": prompt_execution_id,
                "scan_execution_id": scan_execution_id,
                "prompt_id": result.prompt_id,
                "prompt_text": result.prompt_text,
                "raw_response": self._with_reasoning_blob(
                    result.adapter_result.raw_response,
                    result.adapter_result.reasoning,
                ),
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "idempotency_key": prompt_execution_key,
                "parser_version": result.parser_version,
            }

            observation_records: list[ObservationRecord] = []
            for mention_result in result.mention_results:
                observation_key = self._idempotency_key(
                    "observation",
                    prompt_execution_id,
                    str(mention_result.mentioned),
                    str(mention_result.position_in_response),
                    mention_result.context_snippet or "",
                    result.adapter_result.strategy_version,
                )
                observation_records.append(
                    {
                        "id": self._stable_id("observation", observation_key),
                        "prompt_execution_id": prompt_execution_id,
                        "brand_mentioned": mention_result.mentioned,
                        "brand_position": mention_result.position_in_response,
                        "response_excerpt": mention_result.context_snippet or "",
                        "idempotency_key": observation_key,
                        "strategy_version": result.adapter_result.strategy_version,
                    }
                )

            citation_records: list[PromptExecutionCitationRecord] = []
            for citation_payload in result.normalized_citations:
                citation_key = self._idempotency_key(
                    "prompt_execution_citation",
                    prompt_execution_id,
                    citation_payload.url,
                    citation_payload.title,
                    citation_payload.cited_text or "",
                )
                citation_records.append(
                    {
                        "id": self._stable_id("prompt_execution_citation", citation_key),
                        "prompt_execution_id": prompt_execution_id,
                        "url": citation_payload.url,
                        "title": citation_payload.title,
                        "cited_text": citation_payload.cited_text,
                        "idempotency_key": citation_key,
                    }
                )

            for mention_result in result.mention_results:
                mention_record: MentionRecord = {
                    "id": str(uuid.uuid4()),
                    "workspace_id": workspace_id,
                    "run_id": run_id,
                    "brand_id": mention_result.brand_name or self.brand_names[0],
                    "mention_type": "explicit" if mention_result.mentioned else "absent",
                    "text": mention_result.context_snippet or "",
                    "citation": {
                        "url": None,
                        "domain": None,
                        "status": "no_citation",
                    },
                }
                all_mentions.append(mention_record)

            for citation_payload in result.normalized_citations:
                citation_url = citation_payload.url
                citation_record_legacy: MentionRecord = {
                    "id": str(uuid.uuid4()),
                    "workspace_id": workspace_id,
                    "run_id": run_id,
                    "brand_id": self.brand_names[0],
                    "mention_type": "citation",
                    "text": f"Citation from {citation_payload.title}",
                    "citation": {
                        "url": citation_url,
                        "domain": self._domain_from_url(citation_url),
                        "status": "found",
                    },
                }
                all_mentions.append(citation_record_legacy)

            prompt_execution_payloads.append((prompt_execution_record, observation_records, citation_records))

        return {
            "results_count": results_count,
            "failed_prompts": failed_prompts,
            "last_error_message": last_error_message,
            "adapter_results": adapter_results,
            "all_mention_results": all_mention_results,
            "all_citation_results": all_citation_results,
            "all_mentions": all_mentions,
            "prompt_execution_payloads": prompt_execution_payloads,
        }

    def _compute_metrics(
        self,
        results: list[PromptExecutionSuccess | PromptExecutionFailure],
        context: dict[str, object],
    ) -> MetricSnapshotRecord | None:
        successful_results = [result for result in results if isinstance(result, PromptExecutionSuccess)]
        if not successful_results:
            return None

        workspace_id = cast(str, context["workspace_id"])
        run_id = cast(str, context["run_id"])
        prompt_version = cast(str, context["prompt_version"])
        provider_model_name = successful_results[0].adapter_result.model_name

        all_mention_results: list[MentionResult] = []
        all_citation_results: list[CitationResult] = []
        for result in successful_results:
            all_mention_results.extend(result.mention_results)
            all_citation_results.extend(result.citation_results)

        metric_snapshot: MetricSnapshot
        try:
            metric_snapshot = self.metrics_engine.compute(
                workspace_id=workspace_id,
                run_id=run_id,
                mentions=all_mention_results,
                citations=all_citation_results,
                primary_brand=self.brand_names[0],
                prompt_version=prompt_version,
                model=self.model or provider_model_name,
            )
        except TypeError as exc:
            if "primary_brand" not in str(exc):
                raise
            metric_snapshot = self.metrics_engine.compute(
                workspace_id=workspace_id,
                run_id=run_id,
                mentions=all_mention_results,
                citations=all_citation_results,
                prompt_version=prompt_version,
                model=self.model or provider_model_name,
            )

        return {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "brand_id": self.brand_names[0],
            "formula_version": metric_snapshot.formula_version,
            "visibility_score": metric_snapshot.visibility_score,
            "citation_coverage": metric_snapshot.citation_coverage,
            "competitor_wins": metric_snapshot.competitor_wins,
            "mention_count": metric_snapshot.mentioned_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _persist(
        self,
        context: dict[str, object],
        evidence: dict[str, object],
        metrics: MetricSnapshotRecord | None,
        results: list[PromptExecutionSuccess | PromptExecutionFailure],
    ) -> dict[str, object]:
        _ = results

        prisma = context["prisma"]
        run_id = cast(str, context["run_id"])
        workspace_id = cast(str, context["workspace_id"])
        provider_config = cast(ProviderConfig, context["provider_config"])
        started_at = cast(str, context["started_at"])
        prompt_version = cast(str, context["prompt_version"])
        scan_job_id = cast(str, context["scan_job_id"])
        scan_job_idempotency_key = cast(str, context["scan_job_idempotency_key"])
        scan_execution_id = cast(str, context["scan_execution_id"])
        scan_execution_idempotency_key = cast(str, context["scan_execution_idempotency_key"])

        results_count = cast(int, evidence["results_count"])
        failed_prompts = cast(int, evidence["failed_prompts"])
        last_error_message = cast(str | None, evidence["last_error_message"])
        adapter_results = cast(list[AdapterResult], evidence["adapter_results"])
        all_mentions = cast(list[MentionRecord], evidence["all_mentions"])
        prompt_execution_payloads = cast(
            list[tuple[PromptExecutionRecord, list[ObservationRecord], list[PromptExecutionCitationRecord]]],
            evidence["prompt_execution_payloads"],
        )

        status: str
        if results_count == 0:
            status = LifecycleStatus.FAILED.value
        elif failed_prompts > 0:
            status = "completed_with_partial_failures"
        else:
            status = LifecycleStatus.COMPLETED.value

        completed_at = datetime.now(timezone.utc).isoformat()
        provider_name = adapter_results[0].provider if adapter_results else self.provider
        model_name = adapter_results[0].model_name if adapter_results else provider_config.model_name

        scan_job_status = self._normalize_execution_status(status)
        scan_job_record: ScanJobRecord = {
            "id": scan_job_id,
            "workspace_slug": self.workspace_slug,
            "strategy_version": self.strategy.strategy_version,
            "prompt_version": prompt_version,
            "created_at": started_at,
            "idempotency_key": scan_job_idempotency_key,
            "status": scan_job_status,
            "scan_mode": self.strategy.scan_mode.value,
        }
        scan_execution_record: ScanExecutionRecord = {
            "id": scan_execution_id,
            "scan_job_id": scan_job_id,
            "provider": provider_name,
            "model_name": model_name,
            "model_version": adapter_results[0].model_version if adapter_results else provider_config.model_name,
            "executed_at": completed_at,
            "idempotency_key": scan_execution_idempotency_key,
            "status": scan_job_status,
        }

        run_record: RunRecord = {
            "id": run_id,
            "workspace_id": workspace_id,
            "provider": provider_name,
            "model": model_name,
            "prompt_version": prompt_version,
            "parser_version": "parser_v1",
            "status": status,
            "created_at": started_at,
            "raw_response": (
                "\n---\n".join(
                    self._with_reasoning_blob(result.raw_response, result.reasoning) for result in adapter_results
                )
                if adapter_results
                else None
            ),
            "error": last_error_message,
        }

        run_repo = RunRepository(prisma)
        _ = await run_repo.create(run_record)

        evidence_repo = ScanEvidenceRepository(prisma)
        _ = await evidence_repo.create_scan_job(scan_job_record)
        _ = await evidence_repo.create_scan_execution(scan_execution_record)
        for prompt_execution_record, observations, citations in prompt_execution_payloads:
            _ = await evidence_repo.create_prompt_execution(prompt_execution_record)
            for observation in observations:
                _ = await evidence_repo.create_observation(observation)
            for citation in citations:
                _ = await evidence_repo.create_prompt_execution_citation(citation)

        if metrics is not None:
            metric_repo = MetricRepository(prisma)
            _ = await metric_repo.upsert_snapshot(metrics)

        if all_mentions:
            mention_repo = MentionRepository(prisma)
            await mention_repo.create_bulk(all_mentions)

        return {
            "status": status,
            "results_count": results_count,
            "provider_name": provider_name,
            "model_name": model_name,
            "completed_at": completed_at,
            "failed_providers": [provider_name] if failed_prompts > 0 else [],
            "last_error_message": last_error_message,
        }

    async def list_runs(self) -> list[RunRecord]:
        prisma = await get_prisma()
        workspace_repo = WorkspaceRepository(prisma)
        ws = await workspace_repo.get_by_slug(self.workspace_slug)
        if ws is None:
            return []
        run_repo = RunRepository(prisma)
        return await run_repo.list_by_workspace(ws["id"])

    async def _load_competitor_names(self, workspace_id: str) -> list[str]:
        # TODO: migrate competitors table to Prisma schema; for now query via raw SQL
        prisma = await get_prisma()
        try:
            rows = await prisma.query_raw(
                'SELECT "brand_name" FROM "competitors" WHERE "workspace_id" = $1',
                workspace_id,
            )
            return [str(row["brand_name"]) for row in rows if row.get("brand_name")]
        except Exception as e:
            logger.debug(f"[orchestrator] Failed to get competitors: {type(e).__name__}: {e}")
            return []

    @staticmethod
    def _resolve_strategy_provider(provider: str) -> str:
        return resolve_provider_key(provider)

    @staticmethod
    def _idempotency_key(*parts: str) -> str:
        stable_input = "|".join(parts)
        return hashlib.sha256(stable_input.encode("utf-8")).hexdigest()

    @staticmethod
    def _stable_id(namespace: str, key: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{key}"))

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_execution_status(status: str) -> str:
        if status == "completed_with_partial_failures":
            return "completed_with_partial_failures"
        if status == "dry_run":
            return "queued"
        return status

    @staticmethod
    def _build_location_context(workspace: WorkspaceRecord | None) -> LocationContext:
        if workspace is None:
            return LocationContext()
        return LocationContext(
            city=str(workspace.get("city", "") or "").strip(),
            region=str(workspace.get("region", "") or "").strip(),
            country=str(workspace.get("country", "") or "").strip(),
        )

    @staticmethod
    def _domain_from_url(url: str) -> str | None:
        stripped = url.strip()
        if not stripped:
            return None
        without_scheme = stripped.split("://", 1)[1] if "://" in stripped else stripped
        domain = without_scheme.split("/", 1)[0].strip().lower()
        return domain or None

    @staticmethod
    def _with_reasoning_blob(raw_response: str, reasoning: str) -> str:
        if not reasoning.strip():
            return raw_response
        return f"{raw_response}{REASONING_SEPARATOR}{reasoning.strip()}"
