import type { HTMLAttributes } from "react";
import { cn } from "./cn";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {}

/**
 * Base shimmer primitive. Compose it to build any skeleton shape.
 *
 * ```tsx
 * <Skeleton className="h-4 w-32 rounded" />          // text line
 * <Skeleton className="h-10 w-10 rounded-full" />    // avatar circle
 * <Skeleton className="h-2 w-full rounded-full" />   // progress bar
 * ```
 */
function Skeleton({ className, ...props }: SkeletonProps) {
  return <div className={cn("animate-skeleton rounded", className)} {...props} />;
}

export type { SkeletonProps };
export { Skeleton };
