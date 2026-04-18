-- [REQUIRES: pg_partman]
-- [REQUIRES: pg_cron]

SELECT partman.create_parent(
    p_parent_table := 'public.prompt_executions',
    p_control := 'created_at',
    p_interval := '1 month'
)
WHERE EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'prompt_executions'
)
AND NOT EXISTS (
    SELECT 1
    FROM partman.part_config
    WHERE parent_table = 'public.prompt_executions'
);

SELECT partman.create_parent(
    p_parent_table := 'public.observations',
    p_control := 'created_at',
    p_interval := '1 month'
)
WHERE EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'observations'
)
AND NOT EXISTS (
    SELECT 1
    FROM partman.part_config
    WHERE parent_table = 'public.observations'
);

SELECT partman.create_parent(
    p_parent_table := 'public.prompt_execution_citations',
    p_control := 'created_at',
    p_interval := '1 month'
)
WHERE EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'prompt_execution_citations'
)
AND NOT EXISTS (
    SELECT 1
    FROM partman.part_config
    WHERE parent_table = 'public.prompt_execution_citations'
);

CREATE INDEX IF NOT EXISTS idx_brin_scan_jobs_created_at
ON public.scan_jobs USING brin (created_at);

CREATE INDEX IF NOT EXISTS idx_brin_scan_executions_created_at
ON public.scan_executions USING brin (created_at);

CREATE INDEX IF NOT EXISTS idx_brin_prompt_executions_created_at
ON public.prompt_executions USING brin (created_at);

CREATE INDEX IF NOT EXISTS idx_brin_observations_created_at
ON public.observations USING brin (created_at);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_workspace_overview AS
SELECT
    w.slug AS workspace_slug,
    w.id AS workspace_id,
    AVG(ms.visibility_score) AS visibility_score_avg,
    AVG(ms.citation_coverage) AS citation_coverage_avg,
    COALESCE(SUM(ms.mention_count), 0) AS mention_count,
    MAX(sj.created_at) AS last_scan_at
FROM public.workspaces AS w
LEFT JOIN public.metric_snapshots AS ms
    ON ms.workspace_id = w.id
LEFT JOIN public.scan_jobs AS sj
    ON sj.workspace_slug = w.slug
GROUP BY w.slug, w.id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_workspace_overview_workspace_slug
ON public.mv_workspace_overview (workspace_slug);

SELECT cron.schedule(
    'refresh-mv-workspace-overview-hourly',
    '0 * * * *',
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_workspace_overview$$
)
WHERE NOT EXISTS (
    SELECT 1
    FROM cron.job
    WHERE jobname = 'refresh-mv-workspace-overview-hourly'
);

SELECT cron.schedule(
    'vacuum-scan-jobs-nightly',
    '0 3 * * *',
    $$VACUUM (ANALYZE) public.scan_jobs$$
)
WHERE NOT EXISTS (
    SELECT 1
    FROM cron.job
    WHERE jobname = 'vacuum-scan-jobs-nightly'
);
