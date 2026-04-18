CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    brand_name TEXT NOT NULL,
    city TEXT DEFAULT '',
    region TEXT DEFAULT '',
    country TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS brands (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS competitors (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    text TEXT NOT NULL,
    version TEXT,
    created_at TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    raw_response TEXT,
    error TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS mentions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    mention_type TEXT NOT NULL,
    text TEXT NOT NULL,
    citation_url TEXT,
    citation_domain TEXT,
    citation_status TEXT NOT NULL DEFAULT 'no_citation' CHECK (citation_status IN ('found', 'no_citation')),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS metric_snapshots (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    formula_version TEXT NOT NULL,
    visibility_score REAL NOT NULL,
    citation_coverage REAL NOT NULL DEFAULT 0.0,
    competitor_wins INTEGER NOT NULL DEFAULT 0,
    mention_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    rule_triggers_json TEXT,
    created_at TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS scheduler_jobs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    job_name TEXT NOT NULL,
    schedule TEXT,
    payload_json TEXT,
    status TEXT,
    created_at TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS scan_jobs (
    id TEXT PRIMARY KEY,
    workspace_slug TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed_with_partial_failures', 'failed', 'completed')),
    scan_mode TEXT NOT NULL CHECK (scan_mode IN ('onboarding', 'scheduled'))
);

CREATE TABLE IF NOT EXISTS scan_executions (
    id TEXT PRIMARY KEY,
    scan_job_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    executed_at TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (scan_job_id) REFERENCES scan_jobs(id)
);

CREATE TABLE IF NOT EXISTS prompt_executions (
    id TEXT PRIMARY KEY,
    scan_execution_id TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    raw_response TEXT NOT NULL,
    executed_at TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    FOREIGN KEY (scan_execution_id) REFERENCES scan_executions(id)
);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    prompt_execution_id TEXT NOT NULL,
    brand_mentioned INTEGER NOT NULL CHECK (brand_mentioned IN (0, 1)),
    brand_position INTEGER,
    response_excerpt TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    FOREIGN KEY (prompt_execution_id) REFERENCES prompt_executions(id)
);

CREATE TABLE IF NOT EXISTS prompt_execution_citations (
    id TEXT PRIMARY KEY,
    prompt_execution_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    cited_text TEXT,
    idempotency_key TEXT NOT NULL,
    FOREIGN KEY (prompt_execution_id) REFERENCES prompt_executions(id)
);

CREATE TABLE IF NOT EXISTS diagnostic_findings (
    id TEXT PRIMARY KEY,
    workspace_slug TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_refs TEXT NOT NULL,
    created_at TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    applicability_context TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendation_items (
    id TEXT PRIMARY KEY,
    workspace_slug TEXT NOT NULL,
    finding_id TEXT,
    code TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_refs TEXT NOT NULL,
    impact TEXT NOT NULL,
    next_step TEXT NOT NULL,
    confidence REAL NOT NULL,
    rule_version TEXT NOT NULL,
    FOREIGN KEY (finding_id) REFERENCES diagnostic_findings(id)
);

CREATE TABLE IF NOT EXISTS workspace_scan_schedules (
    workspace_id TEXT PRIMARY KEY,
    scan_schedule TEXT NOT NULL DEFAULT 'daily' CHECK (scan_schedule IN ('daily', 'weekly', 'off')),
    updated_at TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS snapshot_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_version TEXT NOT NULL,
    model_version TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_workspace_created_at
ON runs (workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mentions_run_id
ON mentions (run_id);

CREATE INDEX IF NOT EXISTS idx_metric_snapshots_workspace_created_at
ON metric_snapshots (workspace_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_scan_jobs_idempotency_key
ON scan_jobs (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_scan_executions_idempotency_key
ON scan_executions (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_prompt_executions_idempotency_key
ON prompt_executions (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_observations_idempotency_key
ON observations (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_prompt_execution_citations_idempotency_key
ON prompt_execution_citations (idempotency_key);

CREATE INDEX IF NOT EXISTS idx_scan_jobs_workspace_created_at
ON scan_jobs (workspace_slug, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_scan_executions_scan_job_id
ON scan_executions (scan_job_id);

CREATE INDEX IF NOT EXISTS idx_prompt_executions_scan_execution_id
ON prompt_executions (scan_execution_id);

CREATE INDEX IF NOT EXISTS idx_observations_prompt_execution_id
ON observations (prompt_execution_id);

CREATE INDEX IF NOT EXISTS idx_prompt_execution_citations_prompt_execution_id
ON prompt_execution_citations (prompt_execution_id);

CREATE INDEX IF NOT EXISTS idx_diagnostic_findings_workspace_created_at
ON diagnostic_findings (workspace_slug, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recommendation_items_workspace_code
ON recommendation_items (workspace_slug, code);

CREATE INDEX IF NOT EXISTS idx_workspace_scan_schedules_schedule
ON workspace_scan_schedules (scan_schedule);
