import type { MentionTypeItem } from "@citetrack/api-client";
import { RadialBar, RadialBarChart, ResponsiveContainer } from "recharts";
import { ChartContainer, type ChartConfig } from "@citetrack/ui/chart";

interface MentionTypeDonutProps {
  items: MentionTypeItem[];
  totalResponses: number;
}

const chartConfig = {
  mentioned: {
    label: "Mentioned",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export function MentionTypeDonut({ items, totalResponses }: MentionTypeDonutProps) {
  if (totalResponses === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No responses yet.
      </div>
    );
  }

  const mentioned = items.find((i) => i.label === "mentioned")?.count ?? 0;
  const rate = mentioned / totalResponses;
  const pct = Math.round(rate * 100);

  const data = [{ name: "mentioned", value: pct, fill: "var(--chart-1)" }];

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-40 w-40">
        <ChartContainer
          config={chartConfig}
          className="h-full w-full"
          aria-label={`${pct}% of responses mentioned brand`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              data={data}
              innerRadius="68%"
              outerRadius="90%"
              startAngle={90}
              endAngle={90 - 360 * (pct / 100)}
              barSize={14}
            >
              <RadialBar dataKey="value" background isAnimationActive={false} />
            </RadialBarChart>
          </ResponsiveContainer>
        </ChartContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-semibold tabular-nums">{pct}%</div>
          <div className="text-xs text-muted-foreground">mentioned</div>
        </div>
      </div>
      <div className="text-xs text-muted-foreground">
        {mentioned} of {totalResponses} responses
      </div>
    </div>
  );
}
