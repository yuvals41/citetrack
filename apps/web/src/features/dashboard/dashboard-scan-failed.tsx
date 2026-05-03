import type { RunRecord } from "@citetrack/api-client";
import { Button } from "@citetrack/ui/button";
import { AlertCircle, ArrowRight, Loader2 } from "lucide-react";
import { useState } from "react";
import { useRunScan } from "#/features/scans/mutations";

interface DashboardScanFailedProps {
  run: RunRecord;
  workspaceSlug: string | null;
}

export function DashboardScanFailed({ run, workspaceSlug }: DashboardScanFailedProps) {
  const runScan = useRunScan();
  const [retryError, setRetryError] = useState<string | null>(null);

  const handleRetry = () => {
    if (!workspaceSlug) return;
    setRetryError(null);
    runScan.mutate(
      { workspaceSlug },
      {
        onError: (err) => {
          setRetryError(err.message ?? "Retry failed. Please try again.");
        },
      },
    );
  };

  const errorMessage =
    "error_message" in run && run.error_message ? run.error_message : null;

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center p-6">
      <div
        className="w-full max-w-[480px] rounded-2xl bg-background ring-1 ring-foreground/10 shadow-2xl shadow-black/5 p-8 flex flex-col gap-6"
        style={{
          animation: "fadeUpIn 0.35s cubic-bezier(0.32, 0.72, 0, 1) both",
        }}
      >
        <div className="flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 self-start rounded-full bg-foreground/5 px-3 py-1.5 ring-1 ring-foreground/8">
            <AlertCircle className="h-3.5 w-3.5 text-foreground/60" strokeWidth={1.5} />
            <span className="text-[11px] uppercase tracking-widest font-medium text-foreground/50">
              Scan failed
            </span>
          </div>

          <div className="flex flex-col gap-2">
            <h2 className="text-[26px] font-semibold tracking-tight leading-tight">
              First scan didn't
              <br />
              complete
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Something went wrong with the initial scan. Run it again to see how AI cites your
              brand.
            </p>
            {errorMessage ? (
              <p className="text-xs text-muted-foreground/70 font-mono bg-foreground/4 rounded-lg px-3 py-2 ring-1 ring-foreground/6 break-all">
                {errorMessage}
              </p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            size="lg"
            className="w-full h-12 text-base font-medium group transition-all duration-200 active:scale-[0.98]"
            type="button"
            onClick={handleRetry}
            disabled={!workspaceSlug || runScan.isPending}
          >
            {runScan.isPending ? (
              <Loader2 className="animate-spin h-4 w-4" />
            ) : (
              <>
                Retry scan
                <span className="ml-1 flex h-6 w-6 items-center justify-center rounded-full bg-primary-foreground/15 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-px">
                  <ArrowRight className="h-3.5 w-3.5" strokeWidth={2} />
                </span>
              </>
            )}
          </Button>

          {retryError ? (
            <p className="text-center text-xs text-destructive">{retryError}</p>
          ) : (
            <p className="text-center text-[11px] text-muted-foreground">
              ~5 minutes &nbsp;·&nbsp; 6 AI providers &nbsp;·&nbsp; automatic
            </p>
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeUpIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
