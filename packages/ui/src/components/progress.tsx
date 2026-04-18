import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentPropsWithoutRef } from "react";
import { cn } from "./cn";

const progressTrackVariants = cva("relative h-2 w-full overflow-hidden rounded-full bg-surface", {
  variants: {
    size: {
      sm: "h-1.5",
      md: "h-2",
      lg: "h-3",
    },
  },
  defaultVariants: { size: "md" },
});

const progressFillVariants = cva(
  "h-full w-full flex-1 transition-all duration-300 ease-in-out rounded-full",
  {
    variants: {
      variant: {
        default: "bg-primary",
        success: "bg-success",
        warning: "bg-warning",
        destructive: "bg-destructive",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

interface ProgressProps
  extends ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>,
    VariantProps<typeof progressTrackVariants>,
    VariantProps<typeof progressFillVariants> {
  /** 0–100 */
  value?: number;
  /** Show percentage label to the right */
  showLabel?: boolean;
}

function Progress({
  className,
  value = 0,
  size,
  variant,
  showLabel = false,
  ...props
}: ProgressProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <ProgressPrimitive.Root
        className={cn(progressTrackVariants({ size }), "flex-1")}
        value={value}
        {...props}
      >
        <ProgressPrimitive.Indicator
          className={cn(progressFillVariants({ variant }))}
          style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
        />
      </ProgressPrimitive.Root>
      {showLabel && (
        <span className="w-9 shrink-0 text-right text-xs tabular-nums text-foreground-muted">
          {Math.round(value ?? 0)}%
        </span>
      )}
    </div>
  );
}

export type { ProgressProps };
export { Progress };
