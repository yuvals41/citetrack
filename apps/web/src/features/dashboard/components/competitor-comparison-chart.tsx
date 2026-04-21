import type { CompetitorComparisonItem } from "@citetrack/api-client";
import { cn } from "@citetrack/ui/cn";

interface CompetitorComparisonChartProps {
  items: CompetitorComparisonItem[];
}

export function CompetitorComparisonChart({ items }: CompetitorComparisonChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No competitor data yet. Add competitors in Settings and run a scan.
      </div>
    );
  }

  const maxMentions = Math.max(...items.map((item) => item.mentions), 1);

  return (
    <div className="space-y-3" aria-label="Brand and competitor mention counts">
      {items.map((item) => {
        const pct = Math.round((item.mentions / maxMentions) * 100);
        return (
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
            <div
              className="h-2 w-full overflow-hidden rounded-full bg-foreground/5"
              role="progressbar"
              aria-valuenow={item.mentions}
              aria-valuemin={0}
              aria-valuemax={maxMentions}
              aria-label={`${item.name}: ${item.mentions} mentions`}
            >
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  item.is_brand ? "bg-foreground" : "bg-foreground/50",
                )}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
