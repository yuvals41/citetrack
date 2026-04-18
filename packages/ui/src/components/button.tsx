import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "./cn";
import { ShineBorder } from "./shine-border";

const buttonVariants = cva(
  "cursor-pointer inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-ring-offset disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary-hover",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive-hover",
        outline: "border border-border bg-background text-foreground hover:bg-surface",
        secondary: "bg-surface text-foreground hover:bg-surface-hover",
        ghost: "text-foreground hover:bg-surface",
        link: "text-foreground underline-offset-4 hover:underline",
        shine: "bg-primary text-primary-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

/** Inline spinner — inherits `currentColor` so it always matches the button's text color */
function ButtonSpinner() {
  return (
    <span
      aria-hidden="true"
      className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
  );
}

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  /**
   * When true, replaces the button content with a spinner + optional `loadingText`,
   * and disables the button to prevent double-submission.
   * The button retains its current variant colors at reduced opacity so the
   * loading state is clearly relative to each variant.
   */
  isLoading?: boolean;
  /** Text shown next to the spinner while loading. Defaults to "Loading…" */
  loadingText?: string;
}

function Button({
  className,
  variant,
  size,
  asChild = false,
  isLoading = false,
  loadingText = "Loading…",
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  const buttonEl = (
    <Comp
      className={cn(
        buttonVariants({ variant, size, className }),
        isLoading && "opacity-60 cursor-wait",
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <ButtonSpinner />
          {loadingText}
        </>
      ) : (
        children
      )}
    </Comp>
  );

  if (variant === "shine") {
    const isInactive = disabled || isLoading;
    return (
      <span
        className={cn(
          "relative inline-flex rounded-md",
          isInactive ? "p-0" : "p-px",
          isInactive && "opacity-60 cursor-not-allowed",
        )}
      >
        {!isInactive && <ShineBorder borderWidth={2} duration={10} />}
        {buttonEl}
      </span>
    );
  }

  return buttonEl;
}

export type { ButtonProps };
export { Button, buttonVariants };
