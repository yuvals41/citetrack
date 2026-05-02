import type { CompetitorComparisonItem } from "@citetrack/api-client";
import { type ChartConfig, ChartContainer } from "@citetrack/ui/chart";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface CompetitorComparisonChartProps {
  items: CompetitorComparisonItem[];
}

const chartConfig = {
  mentions: {
    label: "Mentions",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export function CompetitorComparisonChart({ items }: CompetitorComparisonChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No competitor data yet. Add competitors in Settings and run a scan.
      </div>
    );
  }

  const data = items.map((item) => ({
    name: item.name,
    mentions: item.mentions,
    is_brand: item.is_brand,
  }));

  return (
    <div className="space-y-3" aria-label="Brand and competitor mention counts">
      {items.map((item) => (
        <div key={item.name} className="space-y-1">
          <div className="flex items-baseline justify-between gap-3">
            <span className="flex items-baseline gap-2 text-sm font-medium">
              {item.name}
              {item.is_brand ? (
                <span className="text-[10px] uppercase tracking-wide rounded-full px-1.5 py-0.5 ring-1 ring-foreground/15 text-muted-foreground">
                  your brand
                </span>
              ) : null}
            </span>
            <span className="text-xs tabular-nums text-muted-foreground">
              {item.mentions} {item.mentions === 1 ? "mention" : "mentions"}
            </span>
          </div>
        </div>
      ))}
      <ChartContainer
        config={chartConfig}
        className="w-full"
        style={{ height: Math.max(items.length * 20, 40) }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            barSize={8}
            accessibilityLayer
          >
            <XAxis type="number" hide domain={[0, "dataMax"]} />
            <YAxis type="category" dataKey="name" hide />
            <Bar dataKey="mentions" radius={[0, 3, 3, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill="var(--chart-1)"
                  fillOpacity={entry.is_brand ? 1 : 0.5}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
