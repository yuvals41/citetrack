import type { TopPageItem } from "@citetrack/api-client";

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

export function TopPagesChart({ items }: TopPagesChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No pages cited yet. Citations come from providers like Perplexity and AI Overviews.
      </div>
    );
  }

  const maxCount = Math.max(...items.map((item) => item.count), 1);

  return (
    <div className="space-y-2.5" aria-label="Top cited pages">
      {items.map((item) => {
        const pct = Math.round((item.count / maxCount) * 100);
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
            <div
              className="h-1.5 w-full overflow-hidden rounded-full bg-foreground/5"
              role="progressbar"
              aria-valuenow={item.count}
              aria-valuemin={0}
              aria-valuemax={maxCount}
            >
              <div className="h-full rounded-full bg-foreground/70" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
