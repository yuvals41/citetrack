import type { HistoricalRunItem } from "@citetrack/api-client";

interface HistoricalMentionsChartProps {
  items: HistoricalRunItem[];
}

const CHART_W = 600;
const CHART_H = 180;
const PAD = { top: 12, right: 16, bottom: 32, left: 36 };
const plotW = CHART_W - PAD.left - PAD.right;
const plotH = CHART_H - PAD.top - PAD.bottom;

function toX(index: number, total: number): number {
  if (total <= 1) return PAD.left + plotW / 2;
  return PAD.left + (index / (total - 1)) * plotW;
}

function toY(value: number, max: number): number {
  if (max <= 0) return PAD.top + plotH;
  const clamped = Math.min(max, Math.max(0, value));
  return PAD.top + plotH - (clamped / max) * plotH;
}

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

  const maxMentions = Math.max(...items.map((item) => item.mentions), 1);
  const coords = items.map((item, idx) => ({
    x: toX(idx, items.length),
    y: toY(item.mentions, maxMentions),
    item,
  }));
  const polyline = coords.map((c) => `${c.x},${c.y}`).join(" ");
  const firstCoord = coords[0];
  const lastCoord = coords[coords.length - 1];
  const baselineY = PAD.top + plotH;
  const areaPath =
    firstCoord !== undefined && lastCoord !== undefined
      ? `M ${firstCoord.x},${firstCoord.y} ${coords
          .slice(1)
          .map((c) => `L ${c.x},${c.y}`)
          .join(" ")} L ${lastCoord.x},${baselineY} L ${firstCoord.x},${baselineY} Z`
      : "";

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((ratio) => Math.round(maxMentions * ratio));

  return (
    <svg
      viewBox={`0 0 ${CHART_W} ${CHART_H}`}
      className="w-full h-48"
      role="img"
      aria-label="Historical mentions chart"
    >
      {gridLines.map((value) => {
        const y = toY(value, maxMentions);
        return (
          <g key={value}>
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
              {value}
            </text>
          </g>
        );
      })}

      {areaPath && <path d={areaPath} fill="currentColor" fillOpacity={0.05} />}

      <polyline
        points={polyline}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {coords.map((c) => (
        <circle
          key={c.item.run_id}
          cx={c.x}
          cy={c.y}
          r={2.5}
          fill="currentColor"
        />
      ))}

      {firstCoord !== undefined && items[0] !== undefined && (
        <text
          x={firstCoord.x}
          y={CHART_H - 6}
          textAnchor="start"
          fontSize={10}
          className="fill-muted-foreground"
          fillOpacity={0.6}
        >
          {formatDate(items[0].run_date)}
        </text>
      )}
      {lastCoord !== undefined && items.length > 1 && items[items.length - 1] !== undefined && (
        <text
          x={lastCoord.x}
          y={CHART_H - 6}
          textAnchor="end"
          fontSize={10}
          className="fill-muted-foreground"
          fillOpacity={0.6}
        >
          {formatDate(items[items.length - 1]!.run_date)}
        </text>
      )}
    </svg>
  );
}
