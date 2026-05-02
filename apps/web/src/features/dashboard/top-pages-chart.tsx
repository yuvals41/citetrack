import type { TopPageItem } from "@citetrack/api-client";
import { type ChartConfig, ChartContainer } from "@citetrack/ui/chart";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface TopPagesChartProps {
  items: TopPageItem[];
}

function shortenUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname === "/" ? "" : parsed.pathname;
    return `${parsed.hostname}${path}`;
  } catch {
    return url;
  }
}

const chartConfig = {
  count: {
    label: "Citations",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export function TopPagesChart({ items }: TopPagesChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No pages cited yet. Citations come from providers like Perplexity and AI Overviews.
      </div>
    );
  }

  const data = items.map((item) => ({
    name: shortenUrl(item.url),
    url: item.url,
    count: item.count,
  }));

  return (
    <div className="space-y-2.5" aria-label="Top cited pages">
      {items.map((item) => {
        const label = shortenUrl(item.url);
        return (
          <div key={item.url} className="space-y-1">
            <div className="flex items-baseline justify-between gap-3">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium truncate hover:underline"
                title={item.url}
              >
                {label}
              </a>
              <span className="text-xs tabular-nums text-muted-foreground">
                {item.count} {item.count === 1 ? "citation" : "citations"}
              </span>
            </div>
          </div>
        );
      })}
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
                <Cell key={entry.url} fill="var(--chart-1)" fillOpacity={0.7} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
