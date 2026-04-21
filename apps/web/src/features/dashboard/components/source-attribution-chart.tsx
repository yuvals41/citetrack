import type { SourceAttributionItem } from "@citetrack/api-client";

interface SourceAttributionChartProps {
  items: SourceAttributionItem[];
}

export function SourceAttributionChart({ items }: SourceAttributionChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No citation sources yet. Citations come from providers like Perplexity and AI Overviews.
      </div>
    );
  }

  const maxCount = Math.max(...items.map((item) => item.count), 1);

  return (
    <div className="space-y-2.5" aria-label="Top citation sources">
      {items.map((item) => {
        const pct = Math.round((item.count / maxCount) * 100);
        return (
          <div key={item.domain} className="space-y-1">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-medium truncate">{item.domain}</span>
              <span className="text-xs tabular-nums text-muted-foreground">
                {item.count} {item.count === 1 ? "citation" : "citations"}
              </span>
            </div>
            <div
              className="h-1.5 w-full overflow-hidden rounded-full bg-foreground/5"
              role="progressbar"
              aria-valuenow={item.count}
              aria-valuemin={0}
              aria-valuemax={maxCount}
              aria-label={`${item.domain} citations ${item.count}`}
            >
              <div className="h-full rounded-full bg-foreground/70" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
