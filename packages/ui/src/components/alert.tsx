import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "./cn";

const alertVariants = cva("flex items-start gap-3 rounded-sm border px-4 py-3 text-sm", {
  variants: {
    variant: {
      info: "border-info-border bg-info-bg text-info-foreground",
      success: "border-success-border bg-success-bg text-success-foreground",
      warning: "border-warning-border bg-warning-bg text-warning-foreground",
      error: "border-error-border bg-error-bg text-error-foreground",
    },
  },
  defaultVariants: {
    variant: "info",
  },
});

const alertIconMap = {
  info: (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className="mt-0.5 shrink-0"
    >
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 7v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="5" r="0.75" fill="currentColor" />
    </svg>
  ),
  success: (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className="mt-0.5 shrink-0"
    >
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M5 8.5l2 2 4-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),
  warning: (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className="mt-0.5 shrink-0"
    >
      <path
        d="M8 2L14.5 13.5H1.5L8 2Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M8 6.5v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="11" r="0.75" fill="currentColor" />
    </svg>
  ),
  error: (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className="mt-0.5 shrink-0"
    >
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M5.5 5.5l5 5M10.5 5.5l-5 5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  ),
} as const;

type AlertVariant = "info" | "success" | "warning" | "error";

interface AlertProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {
  title?: string;
  children?: ReactNode;
  icon?: ReactNode;
}

function Alert({ variant = "info", title, children, icon, className, ...props }: AlertProps) {
  const resolvedVariant: AlertVariant = (variant as AlertVariant) ?? "info";
  const defaultIcon = alertIconMap[resolvedVariant];

  return (
    <div role="alert" className={cn(alertVariants({ variant }), className)} {...props}>
      {icon ?? defaultIcon}
      <div className="flex flex-col gap-0.5">
        {title && <p className="font-semibold leading-tight">{title}</p>}
        {children && <div className="leading-snug opacity-90">{children}</div>}
      </div>
    </div>
  );
}

export type { AlertProps, AlertVariant };
export { Alert, alertVariants };
