import type { ProviderBreakdownItem } from "@citetrack/api-client";
import { type ChartConfig, ChartContainer } from "@citetrack/ui/chart";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface ProviderBreakdownChartProps {
  items: ProviderBreakdownItem[];
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: "ChatGPT",
  anthropic: "Claude",
  perplexity: "Perplexity",
  gemini: "Gemini",
  grok: "Grok",
  google_ai_overview: "AI Overviews",
  google_ai_mode_serpapi: "AI Mode",
};

function providerLabel(key: string): string {
  return PROVIDER_LABELS[key] ?? key;
}

const chartConfig = {
  visibility: {
    label: "Visibility %",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export function ProviderBreakdownChart({ items }: ProviderBreakdownChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No scans yet. Run a scan to see per-provider visibility.
      </div>
    );
  }

  const data = items.map((item) => {
    const rate = item.responses === 0 ? 0 : item.mentions / item.responses;
    const pct = Math.round(rate * 100);
    const noData = item.responses === 0;
    return {
      name: providerLabel(item.provider),
      provider: item.provider,
      visibility: pct,
      noData,
      valueLabel: noData ? "not scanned" : `${item.mentions}/${item.responses} · ${pct}%`,
    };
  });

  return (
    <div className="space-y-3" aria-label="Provider visibility breakdown">
      {data.map((item) => (
        <div key={item.provider} className="space-y-1.5">
          <div className="flex items-baseline justify-between gap-3">
            <span className="text-sm font-medium">{item.name}</span>
            <span className="text-xs tabular-nums text-muted-foreground">{item.valueLabel}</span>
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
            barSize={8}
            accessibilityLayer
          >
            <XAxis type="number" hide domain={[0, 100]} />
            <YAxis type="category" dataKey="name" hide />
            <Bar dataKey="visibility" radius={[0, 3, 3, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.provider}
                  fill="var(--chart-1)"
                  fillOpacity={entry.noData ? 0.15 : 0.7}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
