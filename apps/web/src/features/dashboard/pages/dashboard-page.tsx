import { isDegraded } from "@citetrack/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@citetrack/ui/card";
import { KPICard, KPICardChange, KPICardLabel, KPICardValue } from "@citetrack/ui/kpi-card";
import { Skeleton } from "@citetrack/ui/skeleton";
import { ActionsQueue } from "../components/actions-queue";
import { FindingsList } from "../components/findings-list";
import { HistoricalMentionsChart } from "../components/historical-mentions-chart";
import { MentionTypeDonut } from "../components/mention-type-donut";
import { ProviderBreakdownChart } from "../components/provider-breakdown-chart";
import { SourceAttributionChart } from "../components/source-attribution-chart";
import { TrendIndicator } from "../components/trend-indicator";
import { VisibilityTrendChart } from "../components/visibility-trend-chart";
import {
  useSnapshotActions,
  useSnapshotBreakdowns,
  useSnapshotFindings,
  useSnapshotOverview,
  useSnapshotTrend,
} from "../lib/api-hooks";
import { useMyWorkspaces } from "../lib/workspaces-hooks";

function KPISkeleton() {
  return (
    <KPICard>
      <Skeleton className="h-3 w-2/3 max-w-[140px] rounded-md" />
      <Skeleton className="h-9 w-1/2 max-w-[120px] rounded-md" />
      <Skeleton className="h-3 w-1/3 max-w-[80px] rounded-md" />
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
  const workspacesQuery = useMyWorkspaces();
  const workspaceSlug = workspacesQuery.data?.[0]?.slug ?? null;

  const overview = useSnapshotOverview(workspaceSlug);
  const trend = useSnapshotTrend(workspaceSlug);
  const findings = useSnapshotFindings(workspaceSlug);
  const actions = useSnapshotActions(workspaceSlug);
  const breakdowns = useSnapshotBreakdowns(workspaceSlug);

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

  const breakdownsData =
    breakdowns.data && !isDegraded(breakdowns.data) ? breakdowns.data : null;
  const breakdownsDegraded =
    breakdowns.data && isDegraded(breakdowns.data) ? breakdowns.data.degraded : null;

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Visibility by AI engine</CardTitle>
          </CardHeader>
          <CardContent>
            {breakdowns.isPending ? (
              <div className="space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : breakdowns.error ? (
              <ErrorCard label="breakdowns" message={breakdowns.error.message} />
            ) : breakdownsDegraded ? (
              <p className="text-sm text-muted-foreground py-2">
                {breakdownsDegraded.reason}: {breakdownsDegraded.message}
              </p>
            ) : breakdownsData ? (
              <ProviderBreakdownChart items={breakdownsData.provider_breakdown} />
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Brand presence</CardTitle>
          </CardHeader>
          <CardContent>
            {breakdowns.isPending ? (
              <Skeleton className="h-40 w-40 mx-auto rounded-full" />
            ) : breakdowns.error ? (
              <ErrorCard label="mention types" message={breakdowns.error.message} />
            ) : breakdownsDegraded ? (
              <p className="text-sm text-muted-foreground py-2">
                {breakdownsDegraded.reason}: {breakdownsDegraded.message}
              </p>
            ) : breakdownsData ? (
              <MentionTypeDonut
                items={breakdownsData.mention_types}
                totalResponses={breakdownsData.total_responses}
              />
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Mentions over time</CardTitle>
          </CardHeader>
          <CardContent>
            {breakdowns.isPending ? (
              <Skeleton className="h-48 w-full" />
            ) : breakdowns.error ? (
              <ErrorCard label="historical mentions" message={breakdowns.error.message} />
            ) : breakdownsDegraded ? (
              <p className="text-sm text-muted-foreground py-2">
                {breakdownsDegraded.reason}: {breakdownsDegraded.message}
              </p>
            ) : breakdownsData ? (
              <HistoricalMentionsChart items={breakdownsData.historical_mentions ?? []} />
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top citation sources</CardTitle>
          </CardHeader>
          <CardContent>
            {breakdowns.isPending ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
              </div>
            ) : breakdowns.error ? (
              <ErrorCard label="source attribution" message={breakdowns.error.message} />
            ) : breakdownsDegraded ? (
              <p className="text-sm text-muted-foreground py-2">
                {breakdownsDegraded.reason}: {breakdownsDegraded.message}
              </p>
            ) : breakdownsData ? (
              <SourceAttributionChart items={breakdownsData.source_attribution ?? []} />
            ) : null}
          </CardContent>
        </Card>
      </div>

      {overviewData && overviewData.run_count > 0 ? (
        <TrendIndicator delta={overviewData.trend_delta ?? 0} />
      ) : null}

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
