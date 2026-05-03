import { Card, CardContent, CardHeader, CardTitle } from "@citetrack/ui/card";
import { KPICard, KPICardChange, KPICardLabel, KPICardValue } from "@citetrack/ui/kpi-card";
import { ActionsQueue } from "#/features/actions/actions-queue";
import { FindingsList } from "#/features/actions/findings-list";
import { CompetitorComparisonChart } from "#/features/competitors/competitor-comparison-chart";
import { HistoricalMentionsChart } from "./historical-mentions-chart";
import { MentionTypeDonut } from "./mention-type-donut";
import {
  getFixtureActions,
  getFixtureBreakdowns,
  getFixtureFindings,
  getFixtureOverview,
  getFixtureTrend,
} from "./preview-fixtures";
import { ProviderBreakdownChart } from "./provider-breakdown-chart";
import { SourceAttributionChart } from "./source-attribution-chart";
import { TopPagesChart } from "./top-pages-chart";
import { VisibilityTrendChart } from "./visibility-trend-chart";

function PopulatedDashboardContent() {
  const overview = getFixtureOverview();
  const trend = getFixtureTrend();
  const breakdowns = getFixtureBreakdowns();
  const findings = getFixtureFindings();
  const actions = getFixtureActions();

  const allTrendPoints = trend.items.flatMap((s) => s.points);

  return (
    <main className="flex-1 overflow-auto p-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard>
          <KPICardLabel>Visibility Score</KPICardLabel>
          <KPICardValue>{(overview.visibility_score * 100).toFixed(1)}</KPICardValue>
          <KPICardChange value={4} direction="up" label="vs prev" />
        </KPICard>
        <KPICard>
          <KPICardLabel>Citation Coverage</KPICardLabel>
          <KPICardValue>{(overview.citation_coverage * 100).toFixed(1)}%</KPICardValue>
          <KPICardChange value={0} direction="flat" />
        </KPICard>
        <KPICard>
          <KPICardLabel>Competitor Wins</KPICardLabel>
          <KPICardValue>{overview.competitor_wins}</KPICardValue>
          <KPICardChange value={0} direction="flat" />
        </KPICard>
        <KPICard>
          <KPICardLabel>Total Prompts</KPICardLabel>
          <KPICardValue>{overview.total_prompts}</KPICardValue>
          <KPICardChange value={0} direction="flat" />
        </KPICard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Visibility trend</CardTitle>
          </CardHeader>
          <CardContent>
            <VisibilityTrendChart points={allTrendPoints} />
          </CardContent>
        </Card>

        <div>
          <ActionsQueue actions={actions.items} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Visibility by AI engine</CardTitle>
          </CardHeader>
          <CardContent>
            <ProviderBreakdownChart items={breakdowns.provider_breakdown} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Brand presence</CardTitle>
          </CardHeader>
          <CardContent>
            <MentionTypeDonut
              items={breakdowns.mention_types}
              totalResponses={breakdowns.total_responses}
            />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Mentions over time</CardTitle>
          </CardHeader>
          <CardContent>
            <HistoricalMentionsChart items={breakdowns.historical_mentions ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top citation sources</CardTitle>
          </CardHeader>
          <CardContent>
            <SourceAttributionChart items={breakdowns.source_attribution ?? []} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Competitor comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <CompetitorComparisonChart items={breakdowns.competitor_comparison ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top cited pages</CardTitle>
          </CardHeader>
          <CardContent>
            <TopPagesChart items={breakdowns.top_pages ?? []} />
          </CardContent>
        </Card>
      </div>

      <FindingsList findings={findings.items} />
    </main>
  );
}

export function BlurredDashboardBackground() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none"
      style={{
        filter: "blur(20px)",
        opacity: 0.45,
        transform: "scale(1.06)",
        transformOrigin: "center center",
      }}
    >
      <PopulatedDashboardContent />
    </div>
  );
}

export { PopulatedDashboardContent };
