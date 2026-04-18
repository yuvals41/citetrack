import { cn } from "@citetrack/ui/cn";

interface StepIndicatorProps {
  current: number;
  total: number;
}

export function StepIndicator({ current, total }: StepIndicatorProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            className={cn(
              "size-2 rounded-full",
              i < current
                ? "bg-foreground"
                : i === current
                  ? "bg-foreground ring-4 ring-foreground/10"
                  : "bg-muted",
            )}
          />
        ))}
      </div>
      <p className="text-sm text-muted-foreground">
        Step {current} of {total}
      </p>
    </div>
  );
}
