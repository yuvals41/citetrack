import type { HTMLAttributes } from "react";
import { cn } from "./cn";

/**
 * Shared overlay class string used by Modal, Dialog, Drawer, and MobileSidebar.
 * Import this constant into Radix-based components that render their own
 * `DialogPrimitive.Overlay` (which needs Radix's `data-[state]` attributes).
 */
export const OVERLAY_CLASS = [
  "fixed inset-0 z-50 bg-black/60",
  "data-[state=open]:animate-[dialog-overlay-in_150ms_ease-out_forwards]",
  "data-[state=closed]:animate-[dialog-overlay-out_100ms_ease-in_forwards]",
].join(" ");

/**
 * Standalone backdrop overlay for non-Radix components (e.g. MobileSidebar).
 * Mount/unmount with `AnimatePresence` from `motion/react` for animated entry/exit.
 *
 * ```tsx
 * <AnimatePresence>
 *   {open && <Overlay onClick={close} />}
 * </AnimatePresence>
 * ```
 */
export function Overlay({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("fixed inset-0 z-50 bg-black/60", className)} {...props} />;
}
