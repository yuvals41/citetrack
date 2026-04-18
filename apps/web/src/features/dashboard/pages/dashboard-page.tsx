import { isDegraded } from "@citetrack/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@citetrack/ui/card";
import { KPICard, KPICardChange, KPICardLabel, KPICardValue } from "@citetrack/ui/kpi-card";
import { Skeleton } from "@citetrack/ui/skeleton";
import { ActionsQueue } from "../components/actions-queue";
import { FindingsList } from "../components/findings-list";
import { VisibilityTrendChart } from "../components/visibility-trend-chart";
import {
  useSnapshotActions,
  useSnapshotFindings,
  useSnapshotOverview,
  useSnapshotTrend,
} from "../lib/api-hooks";

function KPISkeleton() {
  return (
    <KPICard>
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-3 w-12" />
    </KPICard>
  );
}

function ErrorCard({ label, message }: { label: string; message: string }) {
  return (
    <Card className="p-4 text-sm text-destructive">
      Failed to load {label}: {message}
    </Card>
  );
}

export function DashboardPage() {
  const overview = useSnapshotOverview();
  const trend = useSnapshotTrend();
  const findings = useSnapshotFindings();
  const actions = useSnapshotActions();

  const overviewData =
    overview.data && !isDegraded(overview.data) ? overview.data : null;
  const overviewDegraded =
    overview.data && isDegraded(overview.data) ? overview.data.degraded : null;

  const trendData = trend.data && !isDegraded(trend.data) ? trend.data : null;
  const trendDegraded = trend.data && isDegraded(trend.data) ? trend.data.degraded : null;

  const findingsData =
    findings.data && !isDegraded(findings.data) ? findings.data : null;
  const findingsDegraded =
    findings.data && isDegraded(findings.data) ? findings.data.degraded : null;

  const actionsData =
    actions.data && !isDegraded(actions.data) ? actions.data : null;
  const actionsDegraded =
    actions.data && isDegraded(actions.data) ? actions.data.degraded : null;

  const trendDelta = overviewData?.trend_delta ?? 0;
  const trendDirection =
    trendDelta > 0 ? ("up" as const) : trendDelta < 0 ? ("down" as const) : ("flat" as const);

  const allTrendPoints = trendData?.items.flatMap((s) => s.points) ?? [];

  return (
    <main className="flex-1 overflow-auto p-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {overview.isPending ? (
          <>
            <KPISkeleton />
            <KPISkeleton />
            <KPISkeleton />
            <KPISkeleton />
          </>
        ) : overview.error ? (
          <div className="col-span-4">
            <ErrorCard label="overview" message={overview.error.message} />
          </div>
        ) : overviewDegraded ? (
          <div className="col-span-4">
            <p className="text-sm text-muted-foreground">{overviewDegraded.reason}: {overviewDegraded.message}</p>
          </div>
        ) : overviewData ? (
          <>
            <KPICard>
              <KPICardLabel>Visibility Score</KPICardLabel>
              <KPICardValue>{(overviewData.visibility_score * 100).toFixed(1)}</KPICardValue>
              <KPICardChange value={Math.round(Math.abs(trendDelta) * 100)} direction={trendDirection} label="vs prev" />
            </KPICard>
            <KPICard>
              <KPICardLabel>Citation Coverage</KPICardLabel>
              <KPICardValue>{(overviewData.citation_coverage * 100).toFixed(1)}%</KPICardValue>
              <KPICardChange value={0} direction="flat" />
            </KPICard>
            <KPICard>
              <KPICardLabel>Competitor Wins</KPICardLabel>
              <KPICardValue>{overviewData.competitor_wins}</KPICardValue>
              <KPICardChange value={0} direction="flat" />
            </KPICard>
            <KPICard>
              <KPICardLabel>Total Prompts</KPICardLabel>
              <KPICardValue>{overviewData.total_prompts}</KPICardValue>
              <KPICardChange value={0} direction="flat" />
            </KPICard>
          </>
        ) : null}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Visibility trend</CardTitle>
          </CardHeader>
          <CardContent>
            {trend.isPending ? (
              <Skeleton className="h-48 w-full" />
            ) : trend.error ? (
              <ErrorCard label="trend" message={trend.error.message} />
            ) : trendDegraded ? (
              <p className="text-sm text-muted-foreground py-2">{trendDegraded.reason}: {trendDegraded.message}</p>
            ) : (
              <VisibilityTrendChart points={allTrendPoints} />
            )}
          </CardContent>
        </Card>

        <div>
          {actions.isPending ? (
            <Card>
              <CardHeader><CardTitle>Top actions</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ) : actions.error ? (
            <ErrorCard label="actions" message={actions.error.message} />
          ) : actionsDegraded ? (
            <Card>
              <CardHeader><CardTitle>Top actions</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground py-2">{actionsDegraded.reason}: {actionsDegraded.message}</p>
              </CardContent>
            </Card>
          ) : actionsData ? (
            <ActionsQueue actions={actionsData.items} />
          ) : null}
        </div>
      </div>

      <div>
        {findings.isPending ? (
          <Card>
            <CardHeader><CardTitle>Findings</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </CardContent>
          </Card>
        ) : findings.error ? (
          <ErrorCard label="findings" message={findings.error.message} />
        ) : findingsDegraded ? (
          <Card>
            <CardHeader><CardTitle>Findings</CardTitle></CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground py-2">{findingsDegraded.reason}: {findingsDegraded.message}</p>
            </CardContent>
          </Card>
        ) : findingsData ? (
          <FindingsList findings={findingsData.items} />
        ) : null}
      </div>
    </main>
  );
}
