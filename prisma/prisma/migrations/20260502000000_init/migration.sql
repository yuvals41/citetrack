-- CreateEnum
CREATE TYPE "RunStatus" AS ENUM ('QUEUED', 'RUNNING', 'COMPLETED', 'COMPLETED_WITH_PARTIAL_FAILURES', 'FAILED');

-- CreateEnum
CREATE TYPE "CitationStatus" AS ENUM ('FOUND', 'NO_CITATION');

-- CreateEnum
CREATE TYPE "ScanStatus" AS ENUM ('QUEUED', 'RUNNING', 'COMPLETED', 'COMPLETED_WITH_PARTIAL_FAILURES', 'FAILED');

-- CreateEnum
CREATE TYPE "ScanMode" AS ENUM ('ONBOARDING', 'SCHEDULED');

-- CreateTable
CREATE TABLE "ai_vis_brands" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_vis_brands_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_competitors" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_vis_competitors_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_mentions" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "run_id" TEXT NOT NULL,
    "brand_id" TEXT NOT NULL,
    "mention_type" TEXT NOT NULL,
    "text" TEXT NOT NULL,
    "citation_url" TEXT,
    "citation_domain" TEXT,
    "citation_status" "CitationStatus" NOT NULL DEFAULT 'NO_CITATION',

    CONSTRAINT "ai_vis_mentions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_metric_snapshots" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "brand_id" TEXT NOT NULL,
    "formula_version" TEXT NOT NULL,
    "visibility_score" DOUBLE PRECISION NOT NULL,
    "citation_coverage" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "competitor_wins" INTEGER NOT NULL DEFAULT 0,
    "mention_count" INTEGER NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_vis_metric_snapshots_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_observations" (
    "id" TEXT NOT NULL,
    "prompt_execution_id" TEXT NOT NULL,
    "brand_mentioned" BOOLEAN NOT NULL,
    "brand_position" INTEGER,
    "response_excerpt" TEXT NOT NULL,
    "idempotency_key" TEXT NOT NULL,
    "strategy_version" TEXT NOT NULL,

    CONSTRAINT "ai_vis_observations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_pixel_events" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "referrer" TEXT,
    "page_url" TEXT,
    "session_id" TEXT,
    "event_type" TEXT NOT NULL DEFAULT 'visit',
    "conversion_value" DOUBLE PRECISION,
    "conversion_currency" TEXT,
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_vis_pixel_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_prompts" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "text" TEXT NOT NULL,
    "version" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_vis_prompts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_prompt_executions" (
    "id" TEXT NOT NULL,
    "scan_execution_id" TEXT NOT NULL,
    "prompt_id" TEXT NOT NULL,
    "prompt_text" TEXT NOT NULL,
    "raw_response" TEXT NOT NULL,
    "executed_at" TIMESTAMP(3) NOT NULL,
    "idempotency_key" TEXT NOT NULL,
    "parser_version" TEXT NOT NULL,

    CONSTRAINT "ai_vis_prompt_executions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_prompt_execution_citations" (
    "id" TEXT NOT NULL,
    "prompt_execution_id" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "cited_text" TEXT,
    "idempotency_key" TEXT NOT NULL,

    CONSTRAINT "ai_vis_prompt_execution_citations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_recommendations" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "brand_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "priority" TEXT NOT NULL,
    "rule_triggers_json" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_vis_recommendations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_runs" (
    "id" TEXT NOT NULL,
    "workspace_id" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "prompt_version" TEXT NOT NULL,
    "parser_version" TEXT NOT NULL,
    "status" "RunStatus" NOT NULL,
    "raw_response" TEXT,
    "error" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_vis_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_scan_executions" (
    "id" TEXT NOT NULL,
    "scan_job_id" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "model_name" TEXT NOT NULL,
    "model_version" TEXT NOT NULL,
    "executed_at" TIMESTAMP(3) NOT NULL,
    "idempotency_key" TEXT NOT NULL,
    "status" TEXT NOT NULL,

    CONSTRAINT "ai_vis_scan_executions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_scan_jobs" (
    "id" TEXT NOT NULL,
    "workspace_slug" TEXT NOT NULL,
    "strategy_version" TEXT NOT NULL,
    "prompt_version" TEXT NOT NULL,
    "idempotency_key" TEXT NOT NULL,
    "status" "ScanStatus" NOT NULL,
    "scan_mode" "ScanMode" NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_vis_scan_jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_workspaces" (
    "id" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "brand_name" TEXT NOT NULL,
    "city" TEXT NOT NULL DEFAULT '',
    "region" TEXT NOT NULL DEFAULT '',
    "country" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_vis_workspaces_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_vis_workspace_schedules" (
    "workspace_id" TEXT NOT NULL,
    "scan_schedule" TEXT NOT NULL CHECK ("scan_schedule" IN ('daily', 'weekly', 'off')),
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_vis_workspace_schedules_pkey" PRIMARY KEY ("workspace_id")
);

-- CreateIndex
CREATE INDEX "ai_vis_brands_workspace_id_idx" ON "ai_vis_brands"("workspace_id");

-- CreateIndex
CREATE INDEX "ai_vis_competitors_workspace_id_idx" ON "ai_vis_competitors"("workspace_id");

-- CreateIndex
CREATE INDEX "ai_vis_mentions_run_id_idx" ON "ai_vis_mentions"("run_id");

-- CreateIndex
CREATE INDEX "ai_vis_mentions_workspace_id_idx" ON "ai_vis_mentions"("workspace_id");

-- CreateIndex
CREATE INDEX "ai_vis_metric_snapshots_workspace_id_created_at_idx" ON "ai_vis_metric_snapshots"("workspace_id", "created_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX "ai_vis_observations_idempotency_key_key" ON "ai_vis_observations"("idempotency_key");

-- CreateIndex
CREATE INDEX "ai_vis_observations_prompt_execution_id_idx" ON "ai_vis_observations"("prompt_execution_id");

-- CreateIndex
CREATE INDEX "idx_ai_vis_pixel_events_workspace_created" ON "ai_vis_pixel_events"("workspace_id", "created_at");

-- CreateIndex
CREATE INDEX "ai_vis_prompts_workspace_id_idx" ON "ai_vis_prompts"("workspace_id");

-- CreateIndex
CREATE UNIQUE INDEX "ai_vis_prompt_executions_idempotency_key_key" ON "ai_vis_prompt_executions"("idempotency_key");

-- CreateIndex
CREATE INDEX "ai_vis_prompt_executions_scan_execution_id_idx" ON "ai_vis_prompt_executions"("scan_execution_id");

-- CreateIndex
CREATE UNIQUE INDEX "ai_vis_prompt_execution_citations_idempotency_key_key" ON "ai_vis_prompt_execution_citations"("idempotency_key");

-- CreateIndex
CREATE INDEX "ai_vis_prompt_execution_citations_prompt_execution_id_idx" ON "ai_vis_prompt_execution_citations"("prompt_execution_id");

-- CreateIndex
CREATE INDEX "ai_vis_recommendations_workspace_id_idx" ON "ai_vis_recommendations"("workspace_id");

-- CreateIndex
CREATE INDEX "ai_vis_runs_workspace_id_created_at_idx" ON "ai_vis_runs"("workspace_id", "created_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX "ai_vis_scan_executions_idempotency_key_key" ON "ai_vis_scan_executions"("idempotency_key");

-- CreateIndex
CREATE INDEX "ai_vis_scan_executions_scan_job_id_idx" ON "ai_vis_scan_executions"("scan_job_id");

-- CreateIndex
CREATE UNIQUE INDEX "ai_vis_scan_jobs_idempotency_key_key" ON "ai_vis_scan_jobs"("idempotency_key");

-- CreateIndex
CREATE INDEX "ai_vis_scan_jobs_workspace_slug_created_at_idx" ON "ai_vis_scan_jobs"("workspace_slug", "created_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX "ai_vis_workspaces_slug_key" ON "ai_vis_workspaces"("slug");

-- CreateIndex
CREATE INDEX "ai_vis_workspaces_slug_idx" ON "ai_vis_workspaces"("slug");

-- CreateIndex
CREATE INDEX "idx_ai_vis_workspace_schedules_schedule" ON "ai_vis_workspace_schedules"("scan_schedule");

-- AddForeignKey
ALTER TABLE "ai_vis_brands" ADD CONSTRAINT "ai_vis_brands_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_competitors" ADD CONSTRAINT "ai_vis_competitors_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_mentions" ADD CONSTRAINT "ai_vis_mentions_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_mentions" ADD CONSTRAINT "ai_vis_mentions_run_id_fkey" FOREIGN KEY ("run_id") REFERENCES "ai_vis_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_metric_snapshots" ADD CONSTRAINT "ai_vis_metric_snapshots_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_observations" ADD CONSTRAINT "ai_vis_observations_prompt_execution_id_fkey" FOREIGN KEY ("prompt_execution_id") REFERENCES "ai_vis_prompt_executions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_prompts" ADD CONSTRAINT "ai_vis_prompts_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_prompt_executions" ADD CONSTRAINT "ai_vis_prompt_executions_scan_execution_id_fkey" FOREIGN KEY ("scan_execution_id") REFERENCES "ai_vis_scan_executions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_prompt_execution_citations" ADD CONSTRAINT "ai_vis_prompt_execution_citations_prompt_execution_id_fkey" FOREIGN KEY ("prompt_execution_id") REFERENCES "ai_vis_prompt_executions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_recommendations" ADD CONSTRAINT "ai_vis_recommendations_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_runs" ADD CONSTRAINT "ai_vis_runs_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_scan_executions" ADD CONSTRAINT "ai_vis_scan_executions_scan_job_id_fkey" FOREIGN KEY ("scan_job_id") REFERENCES "ai_vis_scan_jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_vis_workspace_schedules" ADD CONSTRAINT "ai_vis_workspace_schedules_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE ON UPDATE CASCADE;

