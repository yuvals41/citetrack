import { Link } from "@tanstack/react-router";
import { Route } from "#/routes/_authenticated.dashboard-preview";
import {
  BlurredDashboardBackground,
  PopulatedDashboardContent,
} from "./blurred-dashboard-background";
import { DashboardEmptyState } from "./dashboard-empty-state";
import { DashboardScanInProgress } from "./dashboard-scan-in-progress";

const STATE_LABELS = {
  empty: "empty",
  running: "running",
  populated: "populated",
} as const;

type PreviewState = keyof typeof STATE_LABELS;

function StateToggle({ current }: { current: PreviewState }) {
  const states: PreviewState[] = ["empty", "running", "populated"];

  return (
    <div className="absolute top-3 right-4 z-20 flex items-center gap-1 rounded-full bg-background/95 ring-1 ring-foreground/10 shadow-sm px-1.5 py-1">
      <span className="text-[10px] text-muted-foreground px-1.5 select-none">Preview:</span>
      {states.map((s) => (
        <Link
          key={s}
          to="/dashboard-preview"
          search={{ state: s }}
          className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors duration-150 ${
            current === s
              ? "bg-foreground text-background"
              : "text-muted-foreground hover:text-foreground hover:bg-foreground/5"
          }`}
        >
          {s}
        </Link>
      ))}
    </div>
  );
}

export function DashboardPreviewPage() {
  const { state = "empty" } = Route.useSearch();

  if (state === "populated") {
    return (
      <div className="relative flex-1 overflow-auto">
        <StateToggle current="populated" />
        <PopulatedDashboardContent />
      </div>
    );
  }

  return (
    <div className="relative flex-1 overflow-hidden min-h-0">
      <StateToggle current={state} />

      <BlurredDashboardBackground />

      {state === "empty" ? <DashboardEmptyState /> : <DashboardScanInProgress />}
    </div>
  );
}
