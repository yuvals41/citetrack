import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "./cn";

interface DividerProps extends HTMLAttributes<HTMLDivElement> {
  /** Text or element shown in the center of the divider line */
  label?: ReactNode;
  /** Orientation of the divider */
  orientation?: "horizontal" | "vertical";
}

function Divider({ label, orientation = "horizontal", className, ...props }: DividerProps) {
  if (orientation === "vertical") {
    return (
      <hr
        className={cn("mx-2 inline-block h-full w-px self-stretch border-0 bg-border", className)}
      />
    );
  }

  if (!label) {
    return <hr className={cn("h-px w-full border-0 bg-border", className)} />;
  }

  return (
    <div className={cn("flex w-full items-center gap-4", className)} {...props}>
      <hr className="h-px flex-1 border-0 bg-border" />
      <span className="shrink-0 text-sm text-foreground-muted">{label}</span>
      <hr className="h-px flex-1 border-0 bg-border" />
    </div>
  );
}

export type { DividerProps };
export { Divider };
