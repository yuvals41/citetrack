import type { SourceAttributionItem } from "@citetrack/api-client";
import { type ChartConfig, ChartContainer } from "@citetrack/ui/chart";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface SourceAttributionChartProps {
  items: SourceAttributionItem[];
}

const chartConfig = {
  count: {
    label: "Citations",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export function SourceAttributionChart({ items }: SourceAttributionChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No citation sources yet. Citations come from providers like Perplexity and AI Overviews.
      </div>
    );
  }

  const data = items.map((item) => ({
    name: item.domain,
    count: item.count,
  }));

  return (
    <div className="space-y-2.5" aria-label="Top citation sources">
      {items.map((item) => (
        <div key={item.domain} className="space-y-1">
          <div className="flex items-baseline justify-between gap-3">
            <span className="text-sm font-medium truncate">{item.domain}</span>
            <span className="text-xs tabular-nums text-muted-foreground">
              {item.count} {item.count === 1 ? "citation" : "citations"}
            </span>
          </div>
        </div>
      ))}
      <ChartContainer
        config={chartConfig}
        className="w-full"
        style={{ height: Math.max(data.length * 20, 40) }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            barSize={6}
            accessibilityLayer
          >
            <XAxis type="number" hide domain={[0, "dataMax"]} />
            <YAxis type="category" dataKey="name" hide />
            <Bar dataKey="count" radius={[0, 3, 3, 0]}>
              {data.map((entry) => (
                <Cell key={entry.name} fill="var(--chart-1)" fillOpacity={0.7} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
