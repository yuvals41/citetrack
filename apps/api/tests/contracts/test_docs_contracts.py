"""Contract tests asserting that docs/research-report.md reflects the implemented architecture.

These tests fail if the research report is missing key architectural terms that
describe the actual implemented system. They serve as a living documentation check —
if the architecture changes, the report must be updated too.
"""

from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path(__file__).parent.parent.parent / "docs" / "research-report.md"
RUNBOOK_PATH = Path(__file__).parent.parent.parent / "docs" / "runbooks.md"


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def _runbook_text() -> str:
    return RUNBOOK_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Research report: hybrid provider stack
# ---------------------------------------------------------------------------


def test_report_mentions_hybrid_provider_stack() -> None:
    """Report must describe the hybrid provider stack (not just API-only)."""
    text = _report_text()
    assert "hybrid provider" in text.lower(), "docs/research-report.md must mention 'hybrid provider' stack"


def test_report_mentions_dataforseo_llm_scraper() -> None:
    """Report must mention DataForSEO as a provider."""
    text = _report_text()
    assert "DataForSEO" in text, "docs/research-report.md must mention DataForSEO"


def test_report_mentions_anthropic_web_search() -> None:
    """Report must mention Anthropic web_search tool."""
    text = _report_text()
    assert "web_search" in text or "Anthropic" in text, "docs/research-report.md must mention Anthropic web_search"


def test_report_mentions_perplexity_sonar() -> None:
    """Report must mention Perplexity sonar-pro."""
    text = _report_text()
    assert "sonar-pro" in text or "Perplexity" in text, "docs/research-report.md must mention Perplexity sonar-pro"


# ---------------------------------------------------------------------------
# Research report: evidence pipeline
# ---------------------------------------------------------------------------


def test_report_mentions_evidence_pipeline() -> None:
    """Report must describe the evidence pipeline."""
    text = _report_text()
    assert "evidence pipeline" in text.lower(), "docs/research-report.md must mention 'evidence pipeline'"


def test_report_mentions_scan_job() -> None:
    """Report must mention scan_job as a pipeline stage."""
    text = _report_text()
    assert "scan_job" in text, "docs/research-report.md must mention 'scan_job' pipeline stage"


def test_report_mentions_observation() -> None:
    """Report must mention observation as a pipeline stage."""
    text = _report_text()
    assert "observation" in text, "docs/research-report.md must mention 'observation' pipeline stage"


def test_report_mentions_diagnostic_finding() -> None:
    """Report must mention diagnostic_finding as a pipeline stage."""
    text = _report_text()
    assert "diagnostic_finding" in text, "docs/research-report.md must mention 'diagnostic_finding' pipeline stage"


def test_report_mentions_recommendation_item() -> None:
    """Report must mention recommendation_item as a pipeline stage."""
    text = _report_text()
    assert "recommendation_item" in text, "docs/research-report.md must mention 'recommendation_item' pipeline stage"


# ---------------------------------------------------------------------------
# Research report: PostgreSQL 18 + native add-ons
# ---------------------------------------------------------------------------


def test_report_mentions_pg_partman() -> None:
    """Report must mention pg_partman for table partitioning."""
    text = _report_text()
    assert "pg_partman" in text, "docs/research-report.md must mention 'pg_partman'"


def test_report_mentions_pg_cron() -> None:
    """Report must mention pg_cron for scheduled maintenance."""
    text = _report_text()
    assert "pg_cron" in text, "docs/research-report.md must mention 'pg_cron'"


def test_report_mentions_brin() -> None:
    """Report must mention BRIN indexes for time-series data."""
    text = _report_text()
    assert "BRIN" in text, "docs/research-report.md must mention 'BRIN' indexes"


def test_report_mentions_materialized_views() -> None:
    """Report must mention materialized views for dashboard snapshots."""
    text = _report_text()
    assert "materialized view" in text.lower() or "matview" in text.lower(), (
        "docs/research-report.md must mention materialized views"
    )


def test_report_mentions_postgresql() -> None:
    """Report must mention PostgreSQL as the production database."""
    text = _report_text()
    assert "PostgreSQL" in text, "docs/research-report.md must mention PostgreSQL"


# ---------------------------------------------------------------------------
# Research report: self-serve dashboard and onboarding
# ---------------------------------------------------------------------------


def test_report_mentions_onboarding() -> None:
    """Report must describe the onboarding flow."""
    text = _report_text()
    assert "onboarding" in text.lower(), "docs/research-report.md must mention onboarding"


def test_report_mentions_snapshot_repository() -> None:
    """Report must mention SnapshotRepository as the dashboard data source."""
    text = _report_text()
    assert "SnapshotRepository" in text or "snapshot" in text.lower(), (
        "docs/research-report.md must mention SnapshotRepository"
    )


def test_report_mentions_run_orchestrator() -> None:
    """Report must mention RunOrchestrator as the thin coordinator."""
    text = _report_text()
    assert "RunOrchestrator" in text, "docs/research-report.md must mention RunOrchestrator"


# ---------------------------------------------------------------------------
# Research report: no longer frozen at old API-vs-UI-only framing
# ---------------------------------------------------------------------------


def test_report_has_implemented_architecture_section() -> None:
    """Report must have an 'Implemented Architecture' section (not just 'Recommended')."""
    text = _report_text()
    assert "Implemented Architecture" in text, "docs/research-report.md must have an 'Implemented Architecture' section"


def test_report_version_is_updated() -> None:
    """Report version must be 2.0 or higher (not the original 1.0)."""
    text = _report_text()
    assert "Version: 2.0" in text or "Version:** 2.0" in text, "docs/research-report.md version must be updated to 2.0"


# ---------------------------------------------------------------------------
# Runbook: key operator commands
# ---------------------------------------------------------------------------


def test_runbook_exists() -> None:
    """docs/runbooks.md must exist."""
    assert RUNBOOK_PATH.exists(), "docs/runbooks.md must exist"


def test_runbook_has_health_check_command() -> None:
    """Runbook must document the health check curl command."""
    text = _runbook_text()
    assert "curl" in text and "/api/v1/health" in text, "docs/runbooks.md must document 'curl .../api/v1/health'"


def test_runbook_has_seed_demo_command() -> None:
    """Runbook must document the seed-demo CLI command."""
    text = _runbook_text()
    assert "seed-demo" in text, "docs/runbooks.md must document 'seed-demo' command"


def test_runbook_has_scheduler_dry_run_command() -> None:
    """Runbook must document the scheduler dry-run command."""
    text = _runbook_text()
    assert "run-scheduler" in text and "--dry-run" in text, "docs/runbooks.md must document 'run-scheduler --dry-run'"


def test_runbook_has_common_failure_modes() -> None:
    """Runbook must have a section on common failure modes."""
    text = _runbook_text()
    assert "failure" in text.lower() or "Failure" in text, "docs/runbooks.md must document common failure modes"


def test_runbook_has_release_verification() -> None:
    """Runbook must have a release verification checklist."""
    text = _runbook_text()
    assert "release" in text.lower() and ("checklist" in text.lower() or "verification" in text.lower()), (
        "docs/runbooks.md must have a release verification section"
    )
