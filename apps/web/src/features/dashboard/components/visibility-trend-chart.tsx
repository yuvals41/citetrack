import type { TrendPoint } from "@citetrack/api-client";

interface VisibilityTrendChartProps {
  points: TrendPoint[];
}

const CHART_W = 600;
const CHART_H = 180;
const PAD = { top: 12, right: 16, bottom: 32, left: 36 };

const plotW = CHART_W - PAD.left - PAD.right;
const plotH = CHART_H - PAD.top - PAD.bottom;

const GRID_LINES = [0, 25, 50, 75, 100];

function toX(index: number, total: number): number {
  if (total <= 1) return PAD.left;
  return PAD.left + (index / (total - 1)) * plotW;
}

function toY(score: number): number {
  const clamped = Math.min(100, Math.max(0, score * 100));
  return PAD.top + plotH - (clamped / 100) * plotH;
}

export function VisibilityTrendChart({ points }: VisibilityTrendChartProps) {
  if (points.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-muted-foreground">
        No trend data yet. Run your first scan to see the chart.
      </div>
    );
  }

  const coords = points.map((pt, i) => ({
    x: toX(i, points.length),
    y: toY(pt.visibility_score),
  }));

  const polylinePoints = coords.map((c) => `${c.x},${c.y}`).join(" ");
  const firstCoord = coords[0];
  const lastCoord = coords[coords.length - 1];
  const areaPath =
    firstCoord !== undefined && lastCoord !== undefined
      ? `M ${firstCoord.x},${firstCoord.y} ${coords
          .slice(1)
          .map((c) => `L ${c.x},${c.y}`)
          .join(" ")} L ${lastCoord.x},${PAD.top + plotH} L ${firstCoord.x},${PAD.top + plotH} Z`
      : "";

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  return (
    <svg
      viewBox={`0 0 ${CHART_W} ${CHART_H}`}
      className="w-full h-48"
      aria-label="Visibility trend chart"
      role="img"
    >
      {GRID_LINES.map((val) => {
        const y = toY(val / 100);
        return (
          <g key={val}>
            <line
              x1={PAD.left}
              y1={y}
              x2={PAD.left + plotW}
              y2={y}
              stroke="currentColor"
              strokeOpacity={0.08}
              strokeWidth={1}
            />
            <text
              x={PAD.left - 6}
              y={y}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={10}
              className="fill-muted-foreground"
              fillOpacity={0.6}
            >
              {val}
            </text>
          </g>
        );
      })}

      {areaPath && (
        <path d={areaPath} fill="currentColor" fillOpacity={0.05} />
      )}

      <polyline
        points={polylinePoints}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {firstPoint !== undefined && firstCoord !== undefined && (
        <text
          x={firstCoord.x}
          y={CHART_H - 6}
          textAnchor="start"
          fontSize={10}
          className="fill-muted-foreground"
          fillOpacity={0.6}
        >
          {firstPoint.run_id.slice(0, 8)}
        </text>
      )}
      {lastPoint !== undefined && lastCoord !== undefined && points.length > 1 && (
        <text
          x={lastCoord.x}
          y={CHART_H - 6}
          textAnchor="end"
          fontSize={10}
          className="fill-muted-foreground"
          fillOpacity={0.6}
        >
          {lastPoint.run_id.slice(0, 8)}
        </text>
      )}
    </svg>
  );
}
