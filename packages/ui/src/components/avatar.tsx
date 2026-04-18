import type { ComponentPropsWithoutRef } from "react";
import { useEffect, useState } from "react";
import { cn } from "./cn";
import { Skeleton } from "./skeleton";

type AvatarSize = "sm" | "md" | "lg" | "xl";

interface AvatarProps extends Omit<ComponentPropsWithoutRef<"span">, "children"> {
  src?: string;
  alt?: string;
  name?: string;
  fallback?: string;
  size?: AvatarSize;
}

const avatarSizeMap: Record<AvatarSize, { box: number; font: number }> = {
  sm: { box: 32, font: 13 },
  md: { box: 40, font: 15 },
  lg: { box: 56, font: 20 },
  xl: { box: 72, font: 26 },
};

function getAvatarLetter(name?: string, fallback?: string) {
  const value = (fallback ?? name ?? "").trim();
  const match = value.match(/[\p{L}\p{N}]/u);
  return match?.[0]?.toUpperCase() ?? "?";
}

/**
 * Circle skeleton sized to match the Avatar `size` prop exactly.
 * Use instead of Avatar while the user record is loading.
 *
 * ```tsx
 * {isLoading ? <AvatarSkeleton size="md" /> : <Avatar src={url} name={name} />}
 * ```
 */
function AvatarSkeleton({ size = "md", className }: { size?: AvatarSize; className?: string }) {
  const { box } = avatarSizeMap[size];
  return (
    <Skeleton
      className={cn("shrink-0 rounded-full", className)}
      style={{ width: `${box}px`, height: `${box}px` }}
    />
  );
}

function Avatar({ src, alt, name, fallback, size = "md", className, ...props }: AvatarProps) {
  const [imageFailed, setImageFailed] = useState(!src);
  const { box, font } = avatarSizeMap[size];
  const accessibleLabel = alt ?? name ?? "Avatar";
  const letter = getAvatarLetter(name, fallback);

  useEffect(() => {
    setImageFailed(!src);
  }, [src]);

  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full border border-border bg-foreground text-background",
        className,
      )}
      style={{ width: `${box}px`, height: `${box}px`, fontSize: `${font}px` }}
      {...props}
    >
      {src && !imageFailed ? (
        <img
          src={src}
          alt={accessibleLabel}
          loading="lazy"
          onError={() => setImageFailed(true)}
          className="h-full w-full object-cover"
        />
      ) : (
        <span
          role="img"
          aria-label={accessibleLabel}
          className="inline-flex items-center justify-center font-semibold uppercase"
          style={{ lineHeight: 1 }}
        >
          {letter}
        </span>
      )}
    </span>
  );
}

export type { AvatarProps, AvatarSize };
export { Avatar, AvatarSkeleton };
