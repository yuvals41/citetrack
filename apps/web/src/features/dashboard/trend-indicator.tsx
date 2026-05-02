import { cn } from "@citetrack/ui/cn";
import { Minus, TrendingDown, TrendingUp } from "lucide-react";

interface TrendIndicatorProps {
  delta: number;
  label?: string;
}

export function TrendIndicator({ delta, label = "vs previous scan" }: TrendIndicatorProps) {
  const direction: "up" | "down" | "flat" =
    delta > 0.0001 ? "up" : delta < -0.0001 ? "down" : "flat";

  const Icon = direction === "up" ? TrendingUp : direction === "down" ? TrendingDown : Minus;
  const pts = Math.round(Math.abs(delta) * 100);

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-xl ring-1 ring-foreground/10 p-4 bg-background",
      )}
      aria-label={`Trend indicator: ${direction === "up" ? "up" : direction === "down" ? "down" : "flat"} ${pts} points ${label}`}
    >
      <div
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-full",
          direction === "up" && "bg-foreground/10",
          direction === "down" && "bg-foreground/10",
          direction === "flat" && "bg-foreground/5",
        )}
      >
        <Icon className="size-5" />
      </div>
      <div className="flex flex-col">
        <div className="text-2xl font-semibold tabular-nums leading-none">
          {direction === "up" ? "+" : direction === "down" ? "−" : ""}
          {pts}
          <span className="text-sm font-normal text-muted-foreground"> pts</span>
        </div>
        <div className="text-xs text-muted-foreground mt-1">{label}</div>
      </div>
    </div>
  );
}
