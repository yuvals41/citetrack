import { Info } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "./cn";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

interface InfoTooltipProps {
  /** The tooltip text or content displayed on hover. */
  content: ReactNode;
  /** Icon size in pixels. @default 14 */
  size?: number;
  /** Which side the tooltip opens on. @default "top" */
  side?: "top" | "bottom" | "left" | "right";
  /** Extra class names on the trigger icon wrapper. */
  className?: string;
  /** Maximum width of the tooltip content. @default 220 */
  maxWidth?: number;
}

/**
 * A small info icon (`i`) that shows a tooltip on hover.
 *
 * Wraps itself in `TooltipProvider` so it works standalone — no need
 * for consumers to add a provider higher up.
 *
 * ```tsx
 * <label>Name <InfoTooltip content="This is how teammates see you." /></label>
 * ```
 */
function InfoTooltip({
  content,
  size = 14,
  side = "top",
  className,
  maxWidth = 220,
}: InfoTooltipProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            tabIndex={-1}
            className={cn(
              "inline-flex cursor-help items-center justify-center rounded-full text-foreground-muted transition-colors hover:text-foreground",
              className,
            )}
            aria-label="More information"
          >
            <Info style={{ width: size, height: size }} />
          </button>
        </TooltipTrigger>
        <TooltipContent side={side} style={{ maxWidth }}>
          {content}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export type { InfoTooltipProps };
export { InfoTooltip };
