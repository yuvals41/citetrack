import type { AIResponsesList } from "@citetrack/api-client";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Skeleton } from "@citetrack/ui/skeleton";
import { Quote, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { useRuns } from "#/features/scans/queries";
import { useCurrentWorkspace } from "#/features/workspaces/queries";
import { useResponses } from "./queries";
import { ResponseCard } from "./response-card";

const ALL_RUNS = "__all__";
const RESPONSE_SKELETON_IDS = [
  "response-skeleton-1",
  "response-skeleton-2",
  "response-skeleton-3",
  "response-skeleton-4",
  "response-skeleton-5",
] as const;

interface AIResponsesPageProps {
  workspaceSlug?: string;
}

function formatRunDate(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}

function readRunIdFromUrl(): string {
  if (typeof window === "undefined") {
    return ALL_RUNS;
  }
  return new URLSearchParams(window.location.search).get("runId") ?? ALL_RUNS;
}

function writeRunIdToUrl(runId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  const url = new URL(window.location.href);
  if (runId === ALL_RUNS) {
    url.searchParams.delete("runId");
  } else {
    url.searchParams.set("runId", runId);
  }
  window.history.replaceState({}, "", `${url.pathname}${url.search}`);
}

function ResponseCardSkeleton({ index }: { index: number }) {
  return (
    <Card
      className="rounded-xl border border-foreground/10 p-4"
      data-testid={`response-skeleton-${index}`}
    >
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <Skeleton className="h-6 w-32 rounded-full" />
          <Skeleton className="h-6 w-24 rounded-full" />
        </div>
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <div className="flex justify-end">
          <Skeleton className="h-8 w-32 rounded-md" />
        </div>
      </div>
    </Card>
  );
}

export function AIResponsesPage({ workspaceSlug: propSlug }: AIResponsesPageProps) {
  const { workspace } = useCurrentWorkspace();
  const workspaceSlug = propSlug ?? workspace?.slug ?? "default";
  const [selectedRunId, setSelectedRunId] = useState<string>(readRunIdFromUrl);

  const runs = useRuns(workspaceSlug);
  const responses = useResponses(workspaceSlug, {
    runId: selectedRunId === ALL_RUNS ? undefined : selectedRunId,
  });

  useEffect(() => {
    writeRunIdToUrl(selectedRunId);
  }, [selectedRunId]);

  const runOptions = useMemo(() => {
    const options = [{ value: ALL_RUNS, label: "All runs" }];
    if (!runs.data) {
      return options;
    }

    const seen = new Set<string>();
    for (const run of runs.data.items) {
      if (seen.has(run.id)) {
        continue;
      }
      seen.add(run.id);
      options.push({
        value: run.id,
        label: `${run.provider} · ${run.model} · ${formatRunDate(run.created_at ?? run.started_at)}`,
      });
    }

    return options;
  }, [runs.data]);

  const responsePayload = responses.data;
  const responseData: AIResponsesList | null =
    responsePayload && "items" in responsePayload ? responsePayload : null;
  const degraded =
    responsePayload && "degraded" in responsePayload ? responsePayload.degraded : null;

  return (
    <div className="flex flex-1 flex-col overflow-auto">
      <PageHeader
        title="AI Responses"
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              void responses.refetch();
            }}
            disabled={responses.isFetching}
          >
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        }
      />

      <main className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="flex flex-col gap-3 rounded-xl border border-foreground/10 p-4 md:flex-row md:items-center md:justify-between">
            <label className="flex items-center gap-3 text-sm">
              <span className="text-muted-foreground">Filter by run</span>
              <select
                aria-label="Filter by run"
                value={selectedRunId}
                onChange={(event) => setSelectedRunId(event.target.value)}
                className="min-w-64 rounded-md border border-foreground/10 bg-background px-3 py-2 text-sm outline-none"
              >
                {runOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <p className="text-sm text-muted-foreground">
              {responseData ? responseData.items.length : 0} responses
            </p>
          </div>

          {responses.isPending ? (
            <div data-testid="loading-skeletons" className="space-y-3">
              {RESPONSE_SKELETON_IDS.map((id, index) => (
                <ResponseCardSkeleton key={id} index={index} />
              ))}
            </div>
          ) : responses.error ? (
            <Alert variant="error">Failed to load AI responses: {responses.error.message}</Alert>
          ) : degraded ? (
            <Alert variant="warning">{degraded.message}</Alert>
          ) : responseData && responseData.items.length === 0 ? (
            <Card className="flex flex-col items-center gap-4 rounded-xl border border-foreground/10 p-10 text-center">
              <Quote className="size-12 text-muted-foreground" />
              <div className="space-y-2">
                <h2 className="text-base font-medium">No responses yet</h2>
                <p className="text-sm text-muted-foreground">
                  Responses appear after your first scan completes.
                </p>
              </div>
            </Card>
          ) : responseData ? (
            <div className="space-y-3">
              {responseData.items.map((item) => (
                <ResponseCard key={item.id} item={item} />
              ))}
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
