"""CLI interface for AI Visibility."""

from dotenv import load_dotenv

_ = load_dotenv(override=False)
import asyncio
from importlib import import_module
import json
import os
import sys
from pathlib import Path
from typing import TypeAlias, TypedDict, cast

from loguru import logger
from pydantic import TypeAdapter, ValidationError

from ai_visibility.config import get_settings
from ai_visibility.degraded import DegradedReason, DegradedState as SharedDegradedState, is_degraded
from ai_visibility.extraction import ExtractionPipeline
from ai_visibility.providers import ProviderError
from ai_visibility.metrics import MetricSnapshot as MetricsMetricSnapshot
from ai_visibility.models import (
    Brand,
    CitationRecord,
    Competitor,
    CompetitorComparison,
    ErrorCode,
    FailedProvider,
    Mention,
    MentionType,
    MetricSnapshot,
    Prompt,
    PromptSet,
    PromptVersion,
    Recommendation,
    RuleTrigger,
    Run,
    RunResult,
    RunStatus,
    Workspace,
    WorkspaceCreate,
)
from ai_visibility.prompts import DEFAULT_PROMPTS, PromptLibrary
from ai_visibility.recommendations import RecommendationsEngine
from ai_visibility.runs import RunOrchestrator
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories import MentionRepository, MetricRepository, RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord, RunRecord, MentionRecord

JsonObject: TypeAlias = dict[str, object]
JsonMap: TypeAlias = dict[str, object]
LegacyWorkspaceFallbacks: frozenset[str] = frozenset({"default", "acme", "beta-brand"})


class ProviderInfo(TypedDict):
    configured: list[str]
    available: list[str]
    fallback_chain: list[str]
    count: int


class DoctorResult(TypedDict):
    status: str
    llm_framework: str
    db_path: str
    log_level: str
    providers: ProviderInfo


class PromptListResult(TypedDict):
    status: str
    total_count: int
    categories: list[str]
    prompt_sets: dict[str, list[dict[str, str]]]


class WorkspaceListResult(TypedDict):
    status: str
    total_count: int
    workspaces: list[WorkspaceRecord]


class ParseFixtureResult(TypedDict):
    parser_status: str
    parser_version: str
    mentions: list[dict[str, object]]
    citations: list[dict[str, object]]
    raw_text: str | None
    error_message: str | None


class SummarizeLatestResult(TypedDict):
    workspace: str
    visibility_score: float
    competitor_wins: int
    citation_coverage: float
    formula_version: str


class RunScanResult(TypedDict):
    run_id: str
    workspace_slug: str
    status: str
    results_count: int
    provider: str
    started_at: str


class RunSchedulerResult(TypedDict):
    executed_jobs: int
    results: list[dict[str, object]]


class RecommendLatestResult(TypedDict):
    workspace: str
    recommendations: list[dict[str, object]]
    explanations_enabled: bool


class SeedDemoResult(TypedDict):
    status: str
    workspaces_created: int
    workspaces_skipped: int
    runs_created: int
    mentions_created: int


class DegradedDetails(TypedDict):
    reason: str
    message: str
    recoverable: bool


class DegradedResponse(TypedDict):
    degraded: DegradedDetails


SummarizeLatestOutput: TypeAlias = SummarizeLatestResult | DegradedResponse
RunScanOutput: TypeAlias = RunScanResult | DegradedResponse
RunSchedulerOutput: TypeAlias = RunSchedulerResult | DegradedResponse
RecommendLatestOutput: TypeAlias = RecommendLatestResult | DegradedResponse


def _degraded_response(state: SharedDegradedState | None) -> DegradedResponse:
    if state is None or not is_degraded(state):
        raise ValueError("Degraded state is required")

    return {
        "degraded": {
            "reason": state.reason.value,
            "message": state.message,
            "recoverable": state.recoverable,
        }
    }


def _build_degraded_state(
    reason: DegradedReason,
    message: str,
    *,
    recoverable: bool = True,
    context: JsonMap | None = None,
) -> SharedDegradedState:
    return SharedDegradedState(
        reason=reason,
        message=message,
        recoverable=recoverable,
        context=context,
    )


def _provider_failure_state(
    exc: ProviderError | Exception,
    *,
    context: JsonMap | None = None,
) -> SharedDegradedState:
    reason = DegradedReason.PROVIDER_FAILURE
    if isinstance(exc, ProviderError) and exc.error_code == DegradedReason.MISSING_API_KEY.value:
        reason = DegradedReason.MISSING_API_KEY

    return _build_degraded_state(reason, str(exc), context=context)


async def _allow_legacy_workspace_fallback(workspace: str, repo: WorkspaceRepository) -> bool:
    if workspace not in LegacyWorkspaceFallbacks:
        return False

    return len(await repo.list_all()) == 0


async def _workspace_lookup(
    workspace: str,
    repo: WorkspaceRepository,
) -> tuple[WorkspaceRecord | None, DegradedResponse | None]:
    workspace_record = await repo.get_by_slug(workspace)
    if workspace_record is not None:
        return workspace_record, None

    if await _allow_legacy_workspace_fallback(workspace, repo):
        return None, None

    return None, _degraded_response(
        _build_degraded_state(
            DegradedReason.WORKSPACE_NOT_FOUND,
            f"Workspace not found: {workspace}",
            context={"workspace": workspace},
        )
    )


def doctor(format: str = "json") -> DoctorResult:
    """
    Diagnostic command to report configured providers and environment status.

    Args:
        format: Output format (json or text)

    Returns:
        Dictionary with diagnostic information
    """
    settings = get_settings()
    _ = format

    key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "grok": "XAI_API_KEY",
    }
    configured = settings.providers_list
    available = [provider for provider in configured if os.getenv(key_map.get(provider, ""))]
    if not available:
        available = configured.copy()
    fallback_chain = configured[1:]

    result: DoctorResult = {
        "status": "healthy",
        "llm_framework": settings.llm_framework,
        "db_path": settings.db_path,
        "log_level": settings.log_level,
        "providers": {
            "configured": configured,
            "available": available,
            "fallback_chain": fallback_chain,
            "count": len(available),
        },
    }

    return result


def print_schema(entity: str, _format_arg: str = "json") -> JsonObject:
    """
    Print JSON schema for a domain model.

    Args:
        entity: Entity name (workspace, brand, run, mention, etc.)
        format_arg: Output format (json)

    Returns:
        Dictionary with schema information
    """
    # Map entity names to model classes
    models: dict[str, object] = {
        "workspace": Workspace,
        "workspace_create": WorkspaceCreate,
        "brand": Brand,
        "competitor": Competitor,
        "prompt": Prompt,
        "prompt_version": PromptVersion,
        "prompt_set": PromptSet,
        "mention": Mention,
        "mention_type": MentionType,
        "citation_record": CitationRecord,
        "run": Run,
        "run_status": RunStatus,
        "run_result": RunResult,
        "metric_snapshot": MetricSnapshot,
        "competitor_comparison": CompetitorComparison,
        "recommendation": Recommendation,
        "rule_trigger": RuleTrigger,
        "degraded_reason": DegradedReason,
        "degraded_state": SharedDegradedState,
        "error_code": ErrorCode,
        "failed_provider": FailedProvider,
    }

    if entity not in models:
        return {
            "status": "error",
            "message": f"Unknown entity: {entity}",
            "available_entities": list(models.keys()),
        }

    schema = TypeAdapter(models[entity]).json_schema()

    return {
        "status": "success",
        "entity": entity,
        "schema": schema,
    }


def list_prompts(_format_arg: str = "json") -> PromptListResult:
    """
    List all prompts organized by category.

    Args:
        format_arg: Output format (json or text)

    Returns:
        Dictionary with prompt sets organized by category
    """
    library = PromptLibrary(prompts=DEFAULT_PROMPTS)
    categories = library.list_categories()
    prompt_sets: dict[str, list[dict[str, str]]] = {}
    total_count = 0

    for category in categories:
        prompts = library.get_prompt_set(category)
        prompt_sets[category] = prompts
        total_count += len(prompts)

    result: PromptListResult = {
        "status": "success",
        "total_count": total_count,
        "categories": categories,
        "prompt_sets": prompt_sets,
    }

    return result


async def list_workspaces(_format_arg: str = "json") -> WorkspaceListResult:
    prisma = await get_prisma()
    repo = WorkspaceRepository(prisma)
    workspaces: list[WorkspaceRecord] = await repo.list_all()

    return {
        "status": "success",
        "total_count": len(workspaces),
        "workspaces": workspaces,
    }


def parse_fixture(file_path: str, _format_arg: str = "json") -> ParseFixtureResult:
    _ = _format_arg
    fixture_path = Path(file_path)
    raw_content = fixture_path.read_text(encoding="utf-8")

    extracted_text = raw_content
    if fixture_path.suffix.lower() == ".json":
        try:
            json_payload_adapter: TypeAdapter[object] = TypeAdapter(object)
            payload = json_payload_adapter.validate_json(raw_content)
            if isinstance(payload, dict):
                payload_dict = cast(dict[str, object], payload)
                text_field = payload_dict.get("text")
                content_field = payload_dict.get("content")
                text_value = text_field if isinstance(text_field, str) else content_field
                if isinstance(text_value, str):
                    extracted_text = text_value
                else:
                    extracted_text = json.dumps(payload_dict)
            else:
                extracted_text = json.dumps(payload)
        except ValidationError:
            extracted_text = raw_content

    result = ExtractionPipeline(brand_names=["Acme Corp"]).extract(extracted_text)
    return {
        "parser_status": result.parser_status,
        "parser_version": result.parser_version,
        "mentions": [cast(dict[str, object], mention.model_dump()) for mention in result.mentions],
        "citations": [cast(dict[str, object], citation.model_dump()) for citation in result.citations],
        "raw_text": result.raw_text,
        "error_message": result.error_message,
    }


async def summarize_latest(workspace: str = "default", _format_arg: str = "json") -> SummarizeLatestOutput:
    _ = _format_arg
    prisma = await get_prisma()
    workspace_repo = WorkspaceRepository(prisma)
    run_repo = RunRepository(prisma)
    mention_repo = MentionRepository(prisma)
    metric_repo = MetricRepository(prisma)

    try:
        workspace_record, degraded = await _workspace_lookup(workspace, workspace_repo)
        if degraded is not None:
            return degraded

        if workspace_record is None:
            snapshot = MetricsMetricSnapshot(
                workspace_id=workspace,
                run_id="latest",
                visibility_score=0.0,
                citation_coverage=0.0,
                competitor_wins=0,
                total_prompts=0,
                mentioned_count=0,
            )
            return {
                "workspace": workspace,
                "visibility_score": snapshot.visibility_score,
                "competitor_wins": snapshot.competitor_wins,
                "citation_coverage": snapshot.citation_coverage,
                "formula_version": snapshot.formula_version,
            }

        workspace_id = workspace_record["id"]
        latest_run = await run_repo.get_latest_by_workspace(workspace_id)
        metric_snapshot = await metric_repo.get_latest_by_workspace(workspace_id)
        if latest_run is None or metric_snapshot is None:
            return _degraded_response(
                _build_degraded_state(
                    DegradedReason.EMPTY_HISTORY,
                    f"No completed history found for workspace: {workspace}",
                    context={"workspace": workspace},
                )
            )

        mentions = await mention_repo.list_by_run(latest_run["id"])
        total_mentions = len(mentions)
        found_citations = sum(1 for mention in mentions if mention["citation"]["status"] == "found")
        competitor_wins = sum(1 for mention in mentions if mention["mention_type"] == "competitor")
        citation_coverage = (found_citations / total_mentions) if total_mentions > 0 else 0.0

        return {
            "workspace": workspace,
            "visibility_score": metric_snapshot["visibility_score"],
            "competitor_wins": competitor_wins,
            "citation_coverage": citation_coverage,
            "formula_version": metric_snapshot["formula_version"],
        }
    except Exception as exc:
        return _degraded_response(
            _build_degraded_state(
                DegradedReason.PROVIDER_FAILURE,
                f"Storage unavailable while summarizing workspace {workspace}: {exc}",
                context={"workspace": workspace},
            )
        )


async def run_scan(
    workspace: str = "default",
    provider: str = "openai",
    dry_run: bool = False,
    _format_arg: str = "json",
) -> RunScanOutput:
    _ = _format_arg
    prisma = await get_prisma()
    workspace_repo = WorkspaceRepository(prisma)

    try:
        if not dry_run:
            _workspace_record, degraded = await _workspace_lookup(workspace, workspace_repo)
            if degraded is not None:
                return degraded

        orchestrator = RunOrchestrator(workspace_slug=workspace, provider=provider)
        result = await orchestrator.scan(dry_run=dry_run)
        if result.failed_providers or result.status == "failed":
            reason = DegradedReason.PROVIDER_FAILURE
            error_message = result.error_message or f"Provider failure while running scan for {workspace}"
            if "Missing API key" in error_message:
                reason = DegradedReason.MISSING_API_KEY

            return _degraded_response(
                _build_degraded_state(
                    reason,
                    error_message,
                    context={"workspace": workspace, "provider": provider},
                )
            )

        return {
            "run_id": result.run_id,
            "workspace_slug": result.workspace_slug,
            "status": result.status,
            "results_count": result.results_count,
            "provider": result.provider,
            "started_at": result.started_at,
        }
    except ProviderError as exc:
        return _degraded_response(_provider_failure_state(exc, context={"workspace": workspace, "provider": provider}))
    except Exception as exc:
        return _degraded_response(
            _build_degraded_state(
                DegradedReason.PROVIDER_FAILURE,
                f"Storage unavailable while starting scan for workspace {workspace}: {exc}",
                context={"workspace": workspace, "provider": provider},
            )
        )


async def list_runs(workspace: str = "default", _format_arg: str = "json") -> list[dict[str, object]]:
    _ = _format_arg
    prisma = await get_prisma()
    workspace_repo = WorkspaceRepository(prisma)
    run_repo = RunRepository(prisma)

    try:
        workspace_record, degraded = await _workspace_lookup(workspace, workspace_repo)
        if degraded is not None:
            # For degraded responses, we still need to return a list for CLI compatibility
            # The main() function will handle the error response
            return []

        if workspace_record is None:
            return []

        workspace_id = workspace_record["id"]
        runs = await run_repo.list_by_workspace(workspace_id)
        return [dict(run) for run in runs]
    except Exception as e:
        logger.debug(f"[cli] {type(e).__name__}: {e}")
        # Log error but return empty list for CLI compatibility
        return []


def run_scheduler(
    once: bool = False,
    dry_run: bool = False,
    _format_arg: str = "json",
) -> RunSchedulerOutput:
    _ = _format_arg
    _ = dry_run
    try:
        if once:
            worker_module = import_module("ai_visibility.worker")
            run_scheduled_scans = getattr(worker_module, "run_scheduled_scans")
            asyncio.run(run_scheduled_scans({}))
            return {
                "executed_jobs": 1,
                "results": [{"status": "triggered", "mode": "once"}],
            }

        return {
            "executed_jobs": 0,
            "results": [
                {
                    "status": "idle",
                    "message": "Start the ARQ worker with: arq ai_visibility.worker.WorkerSettings",
                }
            ],
        }
    except Exception as exc:
        return _degraded_response(
            _build_degraded_state(
                DegradedReason.SCHEDULER_MISS,
                f"Unable to execute scheduler run: {exc}",
            )
        )


async def recommend_latest(
    workspace: str = "default",
    disable_explanations: bool = False,
    _format_arg: str = "json",
) -> RecommendLatestOutput:
    _ = _format_arg
    prisma = await get_prisma()
    workspace_repo = WorkspaceRepository(prisma)
    run_repo = RunRepository(prisma)
    mention_repo = MentionRepository(prisma)
    metric_repo = MetricRepository(prisma)

    try:
        workspace_record, degraded = await _workspace_lookup(workspace, workspace_repo)
        if degraded is not None:
            return degraded

        if workspace_record is None:
            return {
                "workspace": workspace,
                "recommendations": [],
                "explanations_enabled": not disable_explanations,
            }

        workspace_id = workspace_record["id"]
        run_records = await run_repo.list_by_workspace(workspace_id)
        if not run_records:
            return {
                "workspace": workspace,
                "recommendations": [],
                "explanations_enabled": not disable_explanations,
            }

        metric_snapshot = await metric_repo.get_latest_by_workspace(workspace_id)
        fallback_visibility = metric_snapshot["visibility_score"] if metric_snapshot is not None else 0.0

        latest_runs: list[dict[str, object]] = []
        for run in run_records[:10]:
            mentions = await mention_repo.list_by_run(run["id"])
            total_mentions = len(mentions)
            brand_mentions = sum(1 for mention in mentions if mention["mention_type"] == "explicit")
            competitor_wins = sum(1 for mention in mentions if mention["mention_type"] == "competitor")
            found_citations = sum(1 for mention in mentions if mention["citation"]["status"] == "found")
            citation_coverage = (found_citations / total_mentions) if total_mentions > 0 else 0.0

            latest_runs.append(
                {
                    "run_id": run["id"],
                    "workspace_slug": workspace,
                    "status": run["status"],
                    "results_count": total_mentions,
                    "provider": run["provider"],
                    "started_at": run["created_at"],
                    "competitor_wins": competitor_wins,
                    "missing_citations": total_mentions - found_citations,
                    "citation_coverage": citation_coverage,
                    "visibility_score": (brand_mentions / total_mentions)
                    if total_mentions > 0
                    else fallback_visibility,
                }
            )

        recommendations = RecommendationsEngine().generate(
            workspace_slug=workspace,
            runs=cast(list[RunResult], latest_runs),
        )
        return {
            "workspace": workspace,
            "recommendations": [
                cast(dict[str, object], recommendation.model_dump()) for recommendation in recommendations
            ],
            "explanations_enabled": not disable_explanations,
        }
    except Exception as exc:
        return _degraded_response(
            _build_degraded_state(
                DegradedReason.PROVIDER_FAILURE,
                f"Storage unavailable while loading recommendations for workspace {workspace}: {exc}",
                context={"workspace": workspace},
            )
        )


class CreateWorkspaceResult(TypedDict):
    status: str
    workspace_id: str
    slug: str
    brand_name: str
    competitors_added: int


async def create_workspace(
    brand_name: str,
    slug: str | None = None,
    domain: str | None = None,
    competitors: list[str] | None = None,
    city: str = "",
    region: str = "",
    country: str = "",
    _format_arg: str = "json",
) -> CreateWorkspaceResult:
    """
    Create a new workspace with optional competitors.

    Args:
        brand_name: Display name for the brand (e.g. 'Maison Remodeling')
        slug: URL-safe slug (auto-generated from brand_name if not provided)
        domain: Brand's website domain (e.g. 'maisonremodeling.com')
        competitors: List of competitor brand names

    Returns:
        Dictionary with workspace creation results
    """
    import re
    import uuid
    from datetime import datetime, timezone

    _ = domain

    prisma = await get_prisma()
    workspace_repo = WorkspaceRepository(prisma)

    # Auto-generate slug from brand_name if not provided
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", brand_name.lower()).strip("-")

    # Check if workspace already exists
    existing = await workspace_repo.get_by_slug(slug)
    if existing is not None:
        logger.info(f"Workspace '{slug}' already exists (id={existing['id']}). Skipping creation.")
        return {
            "status": "already_exists",
            "workspace_id": existing["id"],
            "slug": slug,
            "brand_name": existing["brand_name"],
            "competitors_added": 0,
        }

    workspace_id = str(uuid.uuid4())
    workspace_record: WorkspaceRecord = {
        "id": workspace_id,
        "slug": slug,
        "brand_name": brand_name,
        "city": city,
        "region": region,
        "country": country,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _ = await workspace_repo.create(workspace_record)

    # Insert competitors
    competitors_added = 0
    if competitors:
        for comp_name in competitors:
            comp_id = str(uuid.uuid4())
            now_ts = datetime.now(timezone.utc).isoformat()
            _ = await prisma.execute_raw(
                'INSERT INTO "ai_vis_competitors" ("id", "workspace_id", "name", "domain", "created_at", "updated_at") VALUES ($1, $2, $3, $4, $5::timestamp, $5::timestamp)',
                comp_id,
                workspace_id,
                comp_name,
                "",
                now_ts,
            )
            competitors_added += 1

    return {
        "status": "created",
        "workspace_id": workspace_id,
        "slug": slug,
        "brand_name": brand_name,
        "competitors_added": competitors_added,
    }


async def seed_demo(_format_arg: str = "json") -> SeedDemoResult:
    """
    Seed demo data: create demo workspaces, competitors, and prompts.
    Idempotent: running twice does not create duplicates.

    Args:
        _format_arg: Output format (json)

    Returns:
        Dictionary with seed results
    """
    _ = _format_arg
    from datetime import datetime, timezone
    import uuid

    prisma = await get_prisma()
    workspace_repo = WorkspaceRepository(prisma)
    run_repo = RunRepository(prisma)
    mention_repo = MentionRepository(prisma)

    workspaces_created = 0
    workspaces_skipped = 0
    runs_created = 0
    mentions_created = 0

    # Demo workspace 1: acme
    acme_slug = "acme"
    acme_existing = await workspace_repo.get_by_slug(acme_slug)
    acme_id: str
    if acme_existing is None:
        acme_id = str(uuid.uuid4())
        acme_workspace: WorkspaceRecord = {
            "id": acme_id,
            "slug": acme_slug,
            "brand_name": "Acme Corp",
            "city": "",
            "region": "",
            "country": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _ = await workspace_repo.create(acme_workspace)
        workspaces_created += 1
    else:
        acme_id = acme_existing["id"]
        workspaces_skipped += 1

    # Demo workspace 2: beta-brand
    beta_slug = "beta-brand"
    beta_existing = await workspace_repo.get_by_slug(beta_slug)
    if beta_existing is None:
        beta_id = str(uuid.uuid4())
        beta_workspace: WorkspaceRecord = {
            "id": beta_id,
            "slug": beta_slug,
            "brand_name": "Beta Brand",
            "city": "",
            "region": "",
            "country": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _ = await workspace_repo.create(beta_workspace)
        workspaces_created += 1
    else:
        workspaces_skipped += 1

    # Demo workspace 3: acme-saas (standard B2B SaaS brand, no location)
    acme_saas_slug = "acme-saas"
    acme_saas_existing = await workspace_repo.get_by_slug(acme_saas_slug)
    if acme_saas_existing is None:
        acme_saas_id = str(uuid.uuid4())
        acme_saas_workspace: WorkspaceRecord = {
            "id": acme_saas_id,
            "slug": acme_saas_slug,
            "brand_name": "Acme SaaS",
            "city": "",
            "region": "",
            "country": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _ = await workspace_repo.create(acme_saas_workspace)
        workspaces_created += 1
    else:
        workspaces_skipped += 1

    # Demo workspace 4: local-plumber (local service brand with city+state)
    local_plumber_slug = "local-plumber"
    local_plumber_existing = await workspace_repo.get_by_slug(local_plumber_slug)
    if local_plumber_existing is None:
        local_plumber_id = str(uuid.uuid4())
        local_plumber_workspace: WorkspaceRecord = {
            "id": local_plumber_id,
            "slug": local_plumber_slug,
            "brand_name": "Joe's Plumbing",
            "city": "Denver",
            "region": "Colorado",
            "country": "US",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _ = await workspace_repo.create(local_plumber_workspace)
        workspaces_created += 1
    else:
        workspaces_skipped += 1

    # Demo workspace 5: echo-brand (ambiguous brand name)
    echo_brand_slug = "echo-brand"
    echo_brand_existing = await workspace_repo.get_by_slug(echo_brand_slug)
    if echo_brand_existing is None:
        echo_brand_id = str(uuid.uuid4())
        echo_brand_workspace: WorkspaceRecord = {
            "id": echo_brand_id,
            "slug": echo_brand_slug,
            "brand_name": "Echo",
            "city": "",
            "region": "",
            "country": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _ = await workspace_repo.create(echo_brand_workspace)
        workspaces_created += 1
    else:
        workspaces_skipped += 1

    # Seed runs for acme workspace (idempotent: check if runs already exist)
    existing_runs = await run_repo.list_by_workspace(acme_id)
    if not existing_runs:
        # Create 2 sample runs
        now = datetime.now(timezone.utc)
        for i in range(2):
            run_id = str(uuid.uuid4())
            run: RunRecord = {
                "id": run_id,
                "workspace_id": acme_id,
                "provider": "openai",
                "model": "gpt-4",
                "prompt_version": "v1",
                "parser_version": "parser_v1",
                "status": "completed",
                "created_at": now.isoformat(),
                "raw_response": f"Sample response {i + 1}",
                "error": None,
            }
            if await run_repo.create(run):
                runs_created += 1

    # Seed mentions for acme workspace (idempotent: check if mentions already exist)
    if existing_runs or runs_created > 0:
        # Get the latest run to attach mentions to
        latest_run = await run_repo.get_latest_by_workspace(acme_id)
        if latest_run is not None:
            existing_mentions = await mention_repo.list_by_run(latest_run["id"])
            if not existing_mentions:
                # Create 2 sample mentions
                mentions_to_create: list[MentionRecord] = [
                    {
                        "id": str(uuid.uuid4()),
                        "workspace_id": acme_id,
                        "run_id": latest_run["id"],
                        "brand_id": "brand_acme",
                        "mention_type": "explicit",
                        "text": "Acme Corp is a leader in innovation.",
                        "citation": {
                            "url": "https://example.com/article1",
                            "domain": "example.com",
                            "status": "found",
                        },
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "workspace_id": acme_id,
                        "run_id": latest_run["id"],
                        "brand_id": "brand_competitor",
                        "mention_type": "competitor",
                        "text": "Competitor X offers similar services.",
                        "citation": {
                            "url": None,
                            "domain": None,
                            "status": "no_citation",
                        },
                    },
                ]
                await mention_repo.create_bulk(mentions_to_create)
                mentions_created = len(mentions_to_create)

    return {
        "status": "success",
        "workspaces_created": workspaces_created,
        "workspaces_skipped": workspaces_skipped,
        "runs_created": runs_created,
        "mentions_created": mentions_created,
    }


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        logger.info("Usage: python -m ai_visibility.cli <command> [--format json]")
        sys.exit(1)

    command = sys.argv[1]
    format_arg = "json"
    fixture_path_arg = None
    workspace_arg = "default"
    provider_arg = "openai"
    dry_run_arg = False
    once_arg = False
    disable_explanations_arg = False

    # Parse --format flag
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            format_arg = sys.argv[idx + 1]

    # Parse --entity flag for print-schema
    entity_arg = None
    if "--entity" in sys.argv:
        idx = sys.argv.index("--entity")
        if idx + 1 < len(sys.argv):
            entity_arg = sys.argv[idx + 1]

    if "--workspace" in sys.argv:
        idx = sys.argv.index("--workspace")
        if idx + 1 < len(sys.argv):
            workspace_arg = sys.argv[idx + 1]

    if "--provider" in sys.argv:
        idx = sys.argv.index("--provider")
        if idx + 1 < len(sys.argv):
            provider_arg = sys.argv[idx + 1]

    if "--dry-run" in sys.argv:
        dry_run_arg = True

    if "--once" in sys.argv:
        once_arg = True

    if "--disable-explanations" in sys.argv:
        disable_explanations_arg = True

    # Parse --brand-name flag for create-workspace
    brand_name_arg = None
    if "--brand-name" in sys.argv:
        idx = sys.argv.index("--brand-name")
        if idx + 1 < len(sys.argv):
            brand_name_arg = sys.argv[idx + 1]

    # Parse --domain flag for create-workspace
    domain_arg = None
    if "--domain" in sys.argv:
        idx = sys.argv.index("--domain")
        if idx + 1 < len(sys.argv):
            domain_arg = sys.argv[idx + 1]

    city_arg = ""
    if "--city" in sys.argv:
        idx = sys.argv.index("--city")
        if idx + 1 < len(sys.argv):
            city_arg = sys.argv[idx + 1]

    region_arg = ""
    if "--region" in sys.argv:
        idx = sys.argv.index("--region")
        if idx + 1 < len(sys.argv):
            region_arg = sys.argv[idx + 1]

    country_arg = ""
    if "--country" in sys.argv:
        idx = sys.argv.index("--country")
        if idx + 1 < len(sys.argv):
            country_arg = sys.argv[idx + 1]

    # Parse --competitor flags (repeatable) for create-workspace
    competitor_args: list[str] = []
    for i, arg in enumerate(sys.argv):
        if arg == "--competitor" and i + 1 < len(sys.argv):
            competitor_args.append(sys.argv[i + 1])
    if command == "parse-fixture":
        for idx in range(2, len(sys.argv)):
            arg = sys.argv[idx]
            if arg == "--format":
                continue
            if idx > 2 and sys.argv[idx - 1] == "--format":
                continue
            if not arg.startswith("--"):
                fixture_path_arg = arg
                break

    if command == "doctor":
        doctor_result = doctor(format=format_arg)
        if format_arg == "json":
            output = json.dumps(doctor_result, indent=2)
            logger.debug(f"[cli] doctor output: {output}")
            print(output)
        else:
            logger.info(f"[cli] Status: {doctor_result['status']}")
            logger.info(f"[cli] Status: {doctor_result['status']}")
            logger.info(f"[cli] LLM Framework: {doctor_result['llm_framework']}")
            logger.info(f"[cli] DB Path: {doctor_result['db_path']}")
            logger.info(f"[cli] Log Level: {doctor_result['log_level']}")
            logger.info(f"[cli] Providers: {', '.join(doctor_result['providers']['available'])}")
    elif command == "list-prompts":
        prompts_result = list_prompts(_format_arg=format_arg)
        if format_arg == "json":
            output = json.dumps(prompts_result, indent=2)
            logger.debug(f"[cli] list-prompts output: {output}")
            print(output)
        else:
            logger.info(f"[cli] Total Prompts: {prompts_result['total_count']}")
            logger.info(f"[cli] Status: {prompts_result['status']}")
            logger.info(f"[cli] Total Prompts: {prompts_result['total_count']}")
            logger.info(f"[cli] Categories: {', '.join(prompts_result['categories'])}")
            for category, prompts in prompts_result.get("by_category", {}).items():
                logger.info(f"[cli]   {category}: {len(prompts)} prompts")
    elif command == "list-workspaces":
        workspaces_result = asyncio.run(list_workspaces(_format_arg=format_arg))
        if format_arg == "json":
            output = json.dumps(workspaces_result, indent=2)
            logger.debug(f"[cli] list-workspaces output: {output}")
            print(output)
        else:
            logger.info(f"[cli] Total Workspaces: {workspaces_result['total_count']}")
            logger.info(f"[cli] Status: {workspaces_result['status']}")
            logger.info(f"[cli] Total Workspaces: {workspaces_result['total_count']}")
            for workspace in workspaces_result["workspaces"]:
                logger.info(f"[cli] - {workspace['slug']}: {workspace['brand_name']}")
    elif command == "print-schema":
        if not entity_arg:
            logger.error("[cli] Error: --entity flag is required for print-schema command")
            sys.exit(1)
        schema_result = print_schema(entity=entity_arg, _format_arg=format_arg)
        if format_arg == "json":
            print(json.dumps(schema_result, indent=2))
        else:
            print(json.dumps(schema_result, indent=2))
    elif command == "parse-fixture":
        if not fixture_path_arg:
            logger.error("[cli] Error: file path is required for parse-fixture command")
            sys.exit(1)
        parse_result = parse_fixture(file_path=fixture_path_arg, _format_arg=format_arg)
        if format_arg == "json":
            print(json.dumps(parse_result, indent=2))
        else:
            print(json.dumps(parse_result, indent=2))
    elif command == "summarize-latest":
        summary_result = asyncio.run(summarize_latest(workspace=workspace_arg, _format_arg=format_arg))
        if format_arg == "json":
            print(json.dumps(summary_result, indent=2))
        else:
            print(json.dumps(summary_result, indent=2))
    elif command == "run-scan":
        run_scan_result = asyncio.run(
            run_scan(
                workspace=workspace_arg,
                provider=provider_arg,
                dry_run=dry_run_arg,
                _format_arg=format_arg,
            )
        )
        if format_arg == "json":
            print(json.dumps(run_scan_result, indent=2))
        else:
            print(json.dumps(run_scan_result, indent=2))
    elif command == "list-runs":
        runs_result = asyncio.run(list_runs(workspace=workspace_arg, _format_arg=format_arg))
        if format_arg == "json":
            print(json.dumps(runs_result, indent=2))
        else:
            print(json.dumps(runs_result, indent=2))
    elif command == "run-scheduler":
        scheduler_result = run_scheduler(
            once=once_arg,
            dry_run=dry_run_arg,
            _format_arg=format_arg,
        )
        if format_arg == "json":
            print(json.dumps(scheduler_result, indent=2))
        else:
            print(json.dumps(scheduler_result, indent=2))
    elif command == "recommend-latest":
        recommend_result = asyncio.run(
            recommend_latest(
                workspace=workspace_arg,
                disable_explanations=disable_explanations_arg,
                _format_arg=format_arg,
            )
        )
        if format_arg == "json":
            print(json.dumps(recommend_result, indent=2))
        else:
            print(json.dumps(recommend_result, indent=2))
    elif command == "create-workspace":
        if not brand_name_arg:
            logger.error("[cli] Error: --brand-name is required for create-workspace")
            sys.exit(1)
        result = asyncio.run(
            create_workspace(
                brand_name=brand_name_arg,
                slug=workspace_arg if workspace_arg != "default" else None,
                domain=domain_arg,
                competitors=competitor_args or None,
                city=city_arg,
                region=region_arg,
                country=country_arg,
                _format_arg=format_arg,
            )
        )
        print(json.dumps(result, indent=2))
    elif command == "seed-demo":
        seed_result = asyncio.run(seed_demo(_format_arg=format_arg))
        if format_arg == "json":
            print(json.dumps(seed_result, indent=2))
        else:
            print(json.dumps(seed_result, indent=2))
    else:
        logger.error(f"[cli] Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
