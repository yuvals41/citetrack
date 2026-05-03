import type { RunRecord } from "@citetrack/api-client";
import { Button } from "@citetrack/ui/button";
import { Activity, X } from "lucide-react";

const AI_PROVIDERS = [
  { key: "chatgpt", label: "ChatGPT" },
  { key: "claude", label: "Claude" },
  { key: "perplexity", label: "Perplexity" },
  { key: "gemini", label: "Gemini" },
  { key: "grok", label: "Grok" },
  { key: "ai_overviews", label: "AI Overviews" },
];

interface DashboardScanInProgressProps {
  run?: RunRecord;
}

export function DashboardScanInProgress(_props: DashboardScanInProgressProps = {}) {
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center p-6">
      <div
        className="w-full max-w-[480px] rounded-2xl bg-background ring-1 ring-foreground/10 shadow-2xl shadow-black/5 p-8 flex flex-col gap-6"
        style={{
          animation: "fadeUpIn 0.35s cubic-bezier(0.32, 0.72, 0, 1) both",
        }}
      >
        <div className="flex flex-col gap-4">
          <div
            className="inline-flex items-center gap-2 self-start rounded-full bg-foreground/5 px-3 py-1.5 ring-1 ring-foreground/8"
            style={{ animation: "subtlePulse 2s ease-in-out infinite" }}
          >
            <Activity className="h-3.5 w-3.5 text-foreground/60" strokeWidth={1.5} />
            <span className="text-[11px] uppercase tracking-widest font-medium text-foreground/50">
              Scan in progress
            </span>
          </div>

          <div className="flex flex-col gap-2">
            <h2 className="text-[26px] font-semibold tracking-tight leading-tight">
              Scanning across
              <br />6 AI providers
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              This typically takes about 5 minutes. Results appear here as soon as the scan
              completes.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
            <span>Scanning providers</span>
            <span>~3 min remaining</span>
          </div>

          <div className="h-1 w-full rounded-full bg-foreground/8 overflow-hidden">
            <div
              className="h-full rounded-full bg-foreground/70"
              style={{
                animation: "indeterminateSlide 1.8s cubic-bezier(0.65, 0, 0.35, 1) infinite",
                width: "45%",
              }}
            />
          </div>

          <div className="grid grid-cols-3 gap-2 mt-1">
            {AI_PROVIDERS.map((provider, i) => (
              <div
                key={provider.key}
                className="flex items-center gap-2 rounded-lg bg-foreground/4 px-3 py-2.5 ring-1 ring-foreground/6"
                style={{
                  animation: `providerFadeIn 0.4s cubic-bezier(0.32, 0.72, 0, 1) ${i * 80}ms both`,
                }}
              >
                <span
                  className="h-1.5 w-1.5 shrink-0 rounded-full bg-foreground/40"
                  style={{
                    animation: `dotPulse 1.4s ease-in-out ${i * 200}ms infinite`,
                  }}
                />
                <span className="text-xs font-medium text-foreground/70 truncate">
                  {provider.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between pt-1 border-t border-foreground/6">
          <p className="text-[11px] text-muted-foreground">
            You can leave this page — we'll keep working
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            type="button"
          >
            <X className="h-3.5 w-3.5" strokeWidth={2} />
            Cancel
          </Button>
        </div>
      </div>

      <style>{`
        @keyframes fadeUpIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes subtlePulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.6; }
        }
        @keyframes indeterminateSlide {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
        @keyframes dotPulse {
          0%, 100% { opacity: 0.35; }
          50%       { opacity: 1; }
        }
        @keyframes providerFadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
