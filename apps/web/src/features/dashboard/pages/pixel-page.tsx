import { Link } from "@tanstack/react-router";
import { Wifi } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@citetrack/ui/card";
import { KPICard, KPICardLabel, KPICardValue } from "@citetrack/ui/kpi-card";
import { Skeleton } from "@citetrack/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@citetrack/ui/table";
import { CodeSnippet } from "../components/code-snippet";
import { PageHeader } from "../components/page-header";
import { usePixelSnippet, usePixelStats } from "../lib/pixel-hooks";
import { useMyWorkspaces } from "../lib/workspaces-hooks";

function formatRevenue(value: number): string {
  return "$" + (value ?? 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatConversionRate(visits: number, conversions: number): string {
  if (visits === 0) return "—";
  return ((conversions / visits) * 100).toFixed(1) + "%";
}

function LoadingState() {
  return (
    <main className="flex-1 overflow-auto p-6 space-y-6">
      <Skeleton className="h-48 w-full rounded-lg" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </main>
  );
}

function NoWorkspaceState() {
  return (
    <main className="flex-1 overflow-auto p-6">
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-sm w-full p-8 flex flex-col items-center gap-4 text-center">
          <Wifi className="size-10 text-muted-foreground" />
          <div className="space-y-1">
            <p className="font-medium">No workspace yet</p>
            <p className="text-sm text-muted-foreground">
              Complete onboarding to generate a tracking pixel.
            </p>
          </div>
          <Link to="/onboarding" className="text-sm underline underline-offset-4">
            Complete onboarding
          </Link>
        </Card>
      </div>
    </main>
  );
}

interface PixelContentProps {
  workspaceId: string;
}

function PixelContent({ workspaceId }: PixelContentProps) {
  const snippetQuery = usePixelSnippet(workspaceId);
  const statsQuery = usePixelStats(workspaceId);

  const stats = statsQuery.data;

  const visitsBySource = stats
    ? Object.entries(stats.visits_by_source).sort(([, a], [, b]) => b - a)
    : [];

  const dailyVisits = stats
    ? [...stats.daily_visits].sort((a, b) => b.date.localeCompare(a.date))
    : [];

  return (
    <main className="flex-1 overflow-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Install the pixel on your website</CardTitle>
          <p className="text-sm text-muted-foreground">
            Copy this code and paste it into your website&apos;s &lt;head&gt; tag.
          </p>
        </CardHeader>
        <CardContent>
          {snippetQuery.isPending ? (
            <Skeleton className="h-32 w-full rounded-lg" />
          ) : snippetQuery.error ? (
            <p className="text-sm text-destructive">Failed to load snippet: {snippetQuery.error.message}</p>
          ) : snippetQuery.data ? (
            <CodeSnippet code={snippetQuery.data} language="html" />
          ) : null}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statsQuery.isPending ? (
          <>
            <KPICard><Skeleton className="h-3 w-2/3 rounded-md" /><Skeleton className="h-9 w-1/2 rounded-md" /></KPICard>
            <KPICard><Skeleton className="h-3 w-2/3 rounded-md" /><Skeleton className="h-9 w-1/2 rounded-md" /></KPICard>
            <KPICard><Skeleton className="h-3 w-2/3 rounded-md" /><Skeleton className="h-9 w-1/2 rounded-md" /></KPICard>
            <KPICard><Skeleton className="h-3 w-2/3 rounded-md" /><Skeleton className="h-9 w-1/2 rounded-md" /></KPICard>
          </>
        ) : statsQuery.error ? (
          <div className="col-span-4">
            <p className="text-sm text-destructive">Failed to load stats: {statsQuery.error.message}</p>
          </div>
        ) : stats ? (
          <>
            <KPICard>
              <KPICardLabel>Total Visits</KPICardLabel>
              <KPICardValue>{stats.total_visits}</KPICardValue>
            </KPICard>
            <KPICard>
              <KPICardLabel>Total Conversions</KPICardLabel>
              <KPICardValue>{stats.total_conversions}</KPICardValue>
            </KPICard>
            <KPICard>
              <KPICardLabel>Total Revenue</KPICardLabel>
              <KPICardValue>{formatRevenue(stats.total_revenue)}</KPICardValue>
            </KPICard>
            <KPICard>
              <KPICardLabel>Conversion Rate</KPICardLabel>
              <KPICardValue>{formatConversionRate(stats.total_visits, stats.total_conversions)}</KPICardValue>
            </KPICard>
          </>
        ) : null}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Visits by source</CardTitle>
          </CardHeader>
          <CardContent>
            {statsQuery.isPending ? (
              <Skeleton className="h-32 w-full" />
            ) : visitsBySource.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pixel events yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Source</TableHead>
                    <TableHead>Visits</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visitsBySource.map(([source, count]) => (
                    <TableRow key={source}>
                      <TableCell>{source}</TableCell>
                      <TableCell>{count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Daily visits</CardTitle>
          </CardHeader>
          <CardContent>
            {statsQuery.isPending ? (
              <Skeleton className="h-32 w-full" />
            ) : dailyVisits.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pixel events yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Visits</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dailyVisits.map((row) => (
                    <TableRow key={`${row.date}-${row.source}`}>
                      <TableCell>{row.date}</TableCell>
                      <TableCell>{row.source}</TableCell>
                      <TableCell>{row.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export function PixelPage() {
  const workspacesQuery = useMyWorkspaces();
  const workspaceId = workspacesQuery.data?.[0]?.id ?? null;

  if (workspacesQuery.isPending) {
    return (
      <>
        <PageHeader title="Pixel" />
        <LoadingState />
      </>
    );
  }

  if (!workspaceId) {
    return (
      <>
        <PageHeader title="Pixel" />
        <NoWorkspaceState />
      </>
    );
  }

  return (
    <>
      <PageHeader title="Pixel" />
      <PixelContent workspaceId={workspaceId} />
    </>
  );
}
