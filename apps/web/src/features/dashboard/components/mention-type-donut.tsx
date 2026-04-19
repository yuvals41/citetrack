import type { MentionTypeItem } from "@citetrack/api-client";

interface MentionTypeDonutProps {
  items: MentionTypeItem[];
  totalResponses: number;
}

const SIZE = 160;
const STROKE = 14;
const RADIUS = (SIZE - STROKE) / 2;
const CIRC = 2 * Math.PI * RADIUS;

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
  const offset = CIRC * (1 - rate);

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-40 w-40 -rotate-90"
          role="img"
          aria-label={`${pct}% of responses mentioned brand`}
        >
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            stroke="currentColor"
            strokeOpacity={0.08}
            strokeWidth={STROKE}
            fill="none"
          />
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            stroke="currentColor"
            strokeWidth={STROKE}
            fill="none"
            strokeDasharray={CIRC}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
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
