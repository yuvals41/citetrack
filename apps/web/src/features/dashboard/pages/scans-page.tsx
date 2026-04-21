import { Alert } from "@citetrack/ui/alert";
import { Badge } from "@citetrack/ui/badge";
import { Card } from "@citetrack/ui/card";
import { Skeleton } from "@citetrack/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@citetrack/ui/table";
import { Clock } from "lucide-react";
import { PageHeader } from "../components/page-header";
import { RunScanButton } from "../components/run-scan-button";
import { useRuns } from "../lib/runs-hooks";
import { useMyWorkspaces } from "../lib/workspaces-hooks";
import type { RunRecord } from "@citetrack/api-client";

type RunStatus = RunRecord["status"];

function statusBadge(status: RunStatus) {
  switch (status) {
    case "completed":
      return <Badge variant="default">Done</Badge>;
    case "completed_with_partial_failures":
      return <Badge variant="outline">Partial</Badge>;
    case "failed":
      return <Badge variant="failed">Failed</Badge>;
    case "running":
    case "pending":
      return <Badge variant="outline">Running…</Badge>;
  }
}

function formatTs(ts: string | null | undefined): string {
  if (!ts) return "—";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
}

function LoadingSkeleton() {
  return (
    <Card className="p-0">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Provider</TableHead>
            <TableHead>Model</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Completed</TableHead>
            <TableHead>Error</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 5 }).map((_, i) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: static skeleton
            <TableRow key={i}>
              <TableCell><Skeleton className="h-5 w-20" /></TableCell>
              <TableCell><Skeleton className="h-4 w-32" /></TableCell>
              <TableCell><Skeleton className="h-5 w-16" /></TableCell>
              <TableCell><Skeleton className="h-4 w-36" /></TableCell>
              <TableCell><Skeleton className="h-4 w-36" /></TableCell>
              <TableCell><Skeleton className="h-4 w-24" /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center py-16">
      <div className="flex flex-col items-center gap-5 text-center max-w-md">
        <Clock className="size-12 text-muted-foreground" />
        <div className="flex flex-col gap-2">
          <h2 className="text-base font-semibold">No scans yet</h2>
          <p className="text-sm text-muted-foreground">
            A scan asks AI assistants about your industry and checks if they mention your brand.
            Results take about 30 seconds.
          </p>
        </div>
        <RunScanButton />
      </div>
    </div>
  );
}

function RunsTable({ items }: { items: RunRecord[] }) {
  return (
    <Card className="p-0">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Provider</TableHead>
            <TableHead>Model</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Completed</TableHead>
            <TableHead>Error</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((run) => (
            <TableRow key={run.id}>
              <TableCell>
                <Badge variant="outline">
                  {run.provider.charAt(0).toUpperCase() + run.provider.slice(1)}
                </Badge>
              </TableCell>
              <TableCell>
                <span className="font-mono text-xs text-muted-foreground">{run.model}</span>
              </TableCell>
              <TableCell>{statusBadge(run.status)}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatTs(run.started_at ?? run.created_at)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatTs(run.completed_at)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {run.status === "failed" && run.error_message
                  ? run.error_message.slice(0, 80)
                  : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}

export function ScansPage() {
  const workspacesQuery = useMyWorkspaces();
  const workspaceSlug = workspacesQuery.data?.[0]?.slug ?? "default";
  const { data, isPending, error } = useRuns(workspaceSlug);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <PageHeader
        title="Scans"
        actions={<RunScanButton />}
      />
      <main className="flex-1 overflow-auto p-6 space-y-6">
        {isPending ? (
          <LoadingSkeleton />
        ) : error ? (
          <Alert variant="error">Failed to load scans: {error.message}</Alert>
        ) : !data || data.items.length === 0 ? (
          <EmptyState />
        ) : (
          <RunsTable items={data.items} />
        )}
      </main>
    </div>
  );
}
