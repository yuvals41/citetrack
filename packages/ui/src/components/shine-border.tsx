import type { CSSProperties, HTMLAttributes } from "react";
import { cn } from "./cn";

type ShineBorderVariant = "colorful" | "black" | "white";

const VARIANT_COLORS: Record<ShineBorderVariant, string[]> = {
  colorful: ["#A07CFE", "#FE8FB5", "#FFBE7B"],
  black: ["#000000"],
  white: ["#ffffff"],
};

interface ShineBorderProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Preset color palette for the shine effect.
   * Can be overridden by passing `shineColor` explicitly.
   * @default "colorful"
   */
  variant?: ShineBorderVariant;
  /**
   * Width of the border in pixels.
   * @default 1
   */
  borderWidth?: number;
  /**
   * Duration of the animation in seconds.
   * @default 14
   */
  duration?: number;
  /**
   * Explicit color(s) for the border. Overrides `variant` when provided.
   */
  shineColor?: string | string[];
}

/**
 * Animated shine border effect — matches Magic UI's implementation exactly.
 *
 * Place inside any container with `position: relative` and `overflow: hidden`.
 * The border radius is inherited from the parent automatically.
 *
 * ```tsx
 * <div className="relative overflow-hidden rounded-md">
 *   <ShineBorder />
 *   {children}
 * </div>
 * ```
 */
function ShineBorder({
  variant = "colorful",
  borderWidth = 1,
  duration = 14,
  shineColor,
  className,
  style,
  ...props
}: ShineBorderProps) {
  const colors = shineColor
    ? Array.isArray(shineColor)
      ? shineColor
      : [shineColor]
    : VARIANT_COLORS[variant];

  return (
    <div
      style={
        {
          "--border-width": `${borderWidth}px`,
          "--duration": `${duration}s`,
          backgroundImage: `radial-gradient(transparent,transparent, ${colors.join(",")},transparent,transparent)`,
          backgroundSize: "300% 300%",
          mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
          padding: "var(--border-width)",
          ...style,
        } as CSSProperties
      }
      className={cn(
        "animate-shine pointer-events-none absolute inset-0 size-full rounded-[inherit] will-change-[background-position]",
        className,
      )}
      {...props}
    />
  );
}

export type { ShineBorderProps, ShineBorderVariant };
export { ShineBorder };
