import type { HistoricalRunItem } from "@citetrack/api-client";
import { type ChartConfig, ChartContainer, ChartTooltipContent } from "@citetrack/ui/chart";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface HistoricalMentionsChartProps {
  items: HistoricalRunItem[];
}

const chartConfig = {
  mentions: {
    label: "Mentions",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

function formatDate(iso: string): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  } catch {
    return "";
  }
}

export function HistoricalMentionsChart({ items }: HistoricalMentionsChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-muted-foreground">
        No run history yet.
      </div>
    );
  }

  const data = items.map((item) => ({
    name: formatDate(item.run_date),
    mentions: item.mentions,
  }));

  return (
    <div className="h-48 w-full" role="img" aria-label="Historical mentions chart">
      <ChartContainer config={chartConfig} className="h-full w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} accessibilityLayer>
            <defs>
              <linearGradient id="mentionsFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeOpacity={0.08} vertical={false} />
            <XAxis
              dataKey="name"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10, fill: "currentColor", fillOpacity: 0.6 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10, fill: "currentColor", fillOpacity: 0.6 }}
              width={30}
            />
            <Tooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="mentions"
              stroke="var(--chart-1)"
              strokeWidth={2}
              fill="url(#mentionsFill)"
              dot={{ r: 2.5, fill: "var(--chart-1)", strokeWidth: 0 }}
              activeDot={{ r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
