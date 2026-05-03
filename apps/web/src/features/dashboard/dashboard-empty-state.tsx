import { Button } from "@citetrack/ui/button";
import { ArrowRight, Check, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import { useRunScan } from "#/features/scans/mutations";

const SCAN_CHECKS = [
  "ChatGPT, Claude, Gemini, Perplexity, Grok & AI Overviews",
  "Citations linking back to your pages",
  "Head-to-head mentions vs competitors",
  "Source gaps and indexing blind spots",
];

interface DashboardEmptyStateProps {
  workspaceSlug?: string | null;
}

export function DashboardEmptyState({ workspaceSlug }: DashboardEmptyStateProps = {}) {
  const runScan = useRunScan();
  const [scanError, setScanError] = useState<string | null>(null);

  const handleRunScan = () => {
    if (!workspaceSlug) return;
    setScanError(null);
    runScan.mutate(
      { workspaceSlug },
      {
        onError: (err) => {
          setScanError(err.message ?? "Failed to start scan. Please try again.");
        },
      },
    );
  };
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center p-6">
      <div
        className="w-full max-w-[520px] rounded-2xl bg-background ring-1 ring-foreground/10 shadow-2xl shadow-black/5 p-8 flex flex-col gap-6"
        style={{
          animation: "fadeUpIn 0.35s cubic-bezier(0.32, 0.72, 0, 1) both",
        }}
      >
        <div className="flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 self-start rounded-full bg-foreground/5 px-3 py-1.5 ring-1 ring-foreground/8">
            <Sparkles className="h-3.5 w-3.5 text-foreground/60" strokeWidth={1.5} />
            <span className="text-[11px] uppercase tracking-widest font-medium text-foreground/50">
              No scans yet
            </span>
          </div>

          <div className="flex flex-col gap-2">
            <h2 className="text-[28px] font-semibold tracking-tight leading-tight">
              See how AI cites
              <br />
              your brand
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Run your first scan and we'll check 6 AI providers in parallel — so you see exactly
              where you're cited, where competitors win, and what to fix.
            </p>
          </div>
        </div>

        <ul className="flex flex-col gap-2.5">
          {SCAN_CHECKS.map((item) => (
            <li key={item} className="flex items-center gap-3 text-sm text-foreground/70">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-foreground/6 ring-1 ring-foreground/10">
                <Check className="h-3 w-3" strokeWidth={2.5} />
              </span>
              {item}
            </li>
          ))}
        </ul>

        <div className="flex flex-col gap-3">
          <Button
            size="lg"
            className="w-full h-12 text-base font-medium group transition-all duration-200 active:scale-[0.98]"
            type="button"
            onClick={handleRunScan}
            disabled={!workspaceSlug || runScan.isPending}
          >
            {runScan.isPending ? (
              <Loader2 className="animate-spin h-4 w-4" />
            ) : (
              <>
                Run your first scan
                <span className="ml-1 flex h-6 w-6 items-center justify-center rounded-full bg-primary-foreground/15 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-px">
                  <ArrowRight className="h-3.5 w-3.5" strokeWidth={2} />
                </span>
              </>
            )}
          </Button>

          {scanError ? (
            <p className="text-center text-xs text-destructive">{scanError}</p>
          ) : (
            <p className="text-center text-[11px] text-muted-foreground">
              ~5 minutes &nbsp;·&nbsp; 6 AI providers &nbsp;·&nbsp; automatic
            </p>
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeUpIn {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
