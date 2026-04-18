import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "./cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium leading-tight transition-colors",
  {
    variants: {
      variant: {
        /** Green — live, running, confirmed */
        active: "border-success-border bg-success-bg text-success-foreground",
        /** Green — content visible to end users */
        published: "border-success-border bg-success-bg text-success-foreground",
        /** Amber — awaiting action */
        pending: "border-warning-border bg-warning-bg text-warning-foreground",
        /** Red — something went wrong */
        failed: "border-error-border bg-error-bg text-error-foreground",
        /** Amber — needs attention but not critical */
        warning: "border-warning-border bg-warning-bg text-warning-foreground",
        /** Neutral — work in progress, not yet live */
        draft: "border-neutral-border bg-neutral-bg text-neutral-foreground",
        /** Black — recently created */
        new: "border-primary bg-primary text-primary-foreground",
        /** Blue — identity confirmed */
        verified: "border-info-border bg-info-bg text-info-foreground",
        /** Generic outline */
        outline: "border-border bg-background text-foreground",
        /** Solid black */
        default: "border-primary bg-primary text-primary-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const badgeDotMap: Record<string, string> = {
  active: "bg-success",
  published: "bg-success",
  pending: "bg-warning",
  failed: "bg-destructive",
  warning: "bg-warning",
  draft: "bg-neutral",
  new: "bg-primary-foreground",
  verified: "bg-info",
  outline: "bg-foreground-muted",
  default: "bg-primary-foreground",
};

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  dot?: boolean;
  icon?: React.ReactNode;
}

function Badge({
  variant = "default",
  dot = false,
  icon,
  className,
  children,
  ...props
}: BadgeProps) {
  const resolvedVariant = (variant ?? "default") as BadgeVariant;
  const dotColor = badgeDotMap[resolvedVariant] ?? "bg-foreground";

  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {dot && (
        <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", dotColor)} aria-hidden="true" />
      )}
      {icon && <span className="shrink-0 [&_svg]:size-3">{icon}</span>}
      {children}
    </span>
  );
}

/** Pre-composed semantic badge presets so consumers don't need to pass variant */

function ActiveBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="active" dot {...props}>
      {props.children ?? "Active"}
    </Badge>
  );
}

function PublishedBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="published" dot {...props}>
      {props.children ?? "Published"}
    </Badge>
  );
}

function PendingBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="pending" dot {...props}>
      {props.children ?? "Pending"}
    </Badge>
  );
}

function FailedBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="failed" dot {...props}>
      {props.children ?? "Failed"}
    </Badge>
  );
}

function WarningBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="warning" dot {...props}>
      {props.children ?? "Warning"}
    </Badge>
  );
}

function DraftBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="draft" {...props}>
      {props.children ?? "Draft"}
    </Badge>
  );
}

function NewBadge(props: Omit<BadgeProps, "variant">) {
  return (
    <Badge variant="new" {...props}>
      {props.children ?? "New"}
    </Badge>
  );
}

function VerifiedBadge(props: Omit<BadgeProps, "variant">) {
  const checkIcon = (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
      <path
        d="M2 5l2.5 2.5L8 3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
  return (
    <Badge variant="verified" icon={checkIcon} {...props}>
      {props.children ?? "Verified"}
    </Badge>
  );
}

export type { BadgeProps, BadgeVariant };
export {
  ActiveBadge,
  Badge,
  badgeVariants,
  DraftBadge,
  FailedBadge,
  NewBadge,
  PendingBadge,
  PublishedBadge,
  VerifiedBadge,
  WarningBadge,
};
