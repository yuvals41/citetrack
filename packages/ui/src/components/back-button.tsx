import { ChevronLeft } from "lucide-react";
import type { ComponentProps, ReactNode, Ref } from "react";
import { cn } from "./cn";

export type BackButtonProps = Omit<ComponentProps<"button">, "children"> & {
  /** Accessible label. @default "Go back" */
  label?: string;
  /** Custom icon (defaults to a `ChevronLeft`). */
  icon?: ReactNode;
  ref?: Ref<HTMLButtonElement>;
};

/**
 * Small icon-only bordered back button. Generic — hand it an `onClick` and
 * it fires. Used in mid-flow screens (OTP verify, complete-profile, etc.)
 * as the primary escape hatch. Matches the project's input-like control
 * styling: dark border at rest, deeper border + 4px shadow ring on hover
 * and keyboard focus.
 */
export function BackButton({
  label = "Go back",
  icon,
  className,
  type = "button",
  ref,
  ...props
}: BackButtonProps) {
  return (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      className={cn(
        "inline-flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border border-foreground/20 bg-background text-foreground transition-all",
        "hover:border-foreground hover:shadow-[0_0_0_4px_rgba(0,0,0,0.06)]",
        "focus-visible:border-foreground focus-visible:shadow-[0_0_0_4px_rgba(0,0,0,0.06)] focus-visible:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      {icon ?? <ChevronLeft className="h-5 w-5" aria-hidden />}
    </button>
  );
}
