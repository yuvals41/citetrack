import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { HTMLAttributes } from "react";
import { cn } from "./cn";

function KPICard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-xl bg-card text-card-foreground p-5 ring-1 ring-foreground/10",
        className,
      )}
      {...props}
    />
  );
}
KPICard.displayName = "KPICard";

function KPICardLabel({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "text-xs font-medium text-muted-foreground uppercase tracking-wide",
        className,
      )}
      {...props}
    />
  );
}
KPICardLabel.displayName = "KPICardLabel";

function KPICardValue({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "text-3xl font-semibold tabular-nums leading-tight",
        className,
      )}
      {...props}
    />
  );
}
KPICardValue.displayName = "KPICardValue";

interface KPICardChangeProps {
  value: number;
  direction: "up" | "down" | "flat";
  label?: string;
  className?: string;
}

function KPICardChange({ value, direction, label, className }: KPICardChangeProps) {
  const Icon =
    direction === "up"
      ? ArrowUpRight
      : direction === "down"
        ? ArrowDownRight
        : Minus;

  const colorClass =
    direction === "up" ? "text-foreground" : "text-muted-foreground";

  const sign = direction === "up" ? "+" : direction === "down" ? "-" : "";
  const absValue = Math.abs(value);

  return (
    <div className={cn("flex items-center gap-1 text-xs", colorClass, className)}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>
        {sign}
        {absValue}%
      </span>
      {label && <span className="text-muted-foreground">{label}</span>}
    </div>
  );
}
KPICardChange.displayName = "KPICardChange";

function KPICardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("text-xs text-muted-foreground", className)}
      {...props}
    />
  );
}
KPICardFooter.displayName = "KPICardFooter";

export type { KPICardChangeProps };
export { KPICard, KPICardLabel, KPICardValue, KPICardChange, KPICardFooter };
