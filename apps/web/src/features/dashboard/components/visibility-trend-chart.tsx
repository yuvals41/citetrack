import type { TrendPoint } from "@citetrack/api-client";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ChartContainer,
  ChartTooltipContent,
  type ChartConfig,
} from "@citetrack/ui/chart";

interface VisibilityTrendChartProps {
  points: TrendPoint[];
}

const chartConfig = {
  visibility: {
    label: "Visibility",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

function formatRunId(runId: string): string {
  return runId.slice(0, 8);
}

export function VisibilityTrendChart({ points }: VisibilityTrendChartProps) {
  if (points.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-muted-foreground">
        No trend data yet. Run your first scan to see the chart.
      </div>
    );
  }

  const data = points.map((pt) => ({
    name: formatRunId(pt.run_id),
    visibility: Math.round(pt.visibility_score * 100),
  }));

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  return (
    <div role="img" aria-label="Visibility trend chart" className="w-full">
      <ChartContainer config={chartConfig} className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} accessibilityLayer>
            <defs>
              <linearGradient id="visibilityFill" x1="0" y1="0" x2="0" y2="1">
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
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10, fill: "currentColor", fillOpacity: 0.6 }}
              width={30}
            />
            <Tooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="visibility"
              stroke="var(--chart-1)"
              strokeWidth={2}
              fill="url(#visibilityFill)"
              dot={{ r: 2.5, fill: "var(--chart-1)", strokeWidth: 0 }}
              activeDot={{ r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartContainer>
      {firstPoint !== undefined && (
        <div className="flex justify-between mt-1 px-1 text-[10px] text-muted-foreground/60 select-none">
          <span>{formatRunId(firstPoint.run_id)}</span>
          {lastPoint !== undefined && points.length > 1 && (
            <span>{formatRunId(lastPoint.run_id)}</span>
          )}
        </div>
      )}
    </div>
  );
}
