import type { ProviderBreakdownItem } from "@citetrack/api-client";

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

export function ProviderBreakdownChart({ items }: ProviderBreakdownChartProps) {
  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No scans yet. Run a scan to see per-provider visibility.
      </div>
    );
  }

  return (
    <div className="space-y-3" aria-label="Provider visibility breakdown">
      {items.map((item) => {
        const rate = item.responses === 0 ? 0 : item.mentions / item.responses;
        const pct = Math.round(rate * 100);
        const noData = item.responses === 0;
        return (
          <div key={item.provider} className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-medium">{providerLabel(item.provider)}</span>
              <span className="text-xs tabular-nums text-muted-foreground">
                {noData ? "not scanned" : `${item.mentions}/${item.responses} · ${pct}%`}
              </span>
            </div>
            <div
              className="h-2 w-full overflow-hidden rounded-full bg-foreground/5"
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${providerLabel(item.provider)} visibility ${pct}%`}
            >
              <div
                className="h-full rounded-full bg-foreground/70 transition-all"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
