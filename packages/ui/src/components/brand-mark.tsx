import type { ImgHTMLAttributes } from "react";
import { cn } from "./cn";

type BrandMarkProps = Omit<ImgHTMLAttributes<HTMLImageElement>, "src" | "alt"> & {
  variant?: "light" | "dark";
  alt?: string;
};

export function BrandMark({
  variant = "light",
  className,
  alt = "Citetrack AI",
  ...rest
}: BrandMarkProps) {
  return (
    <img
      src={`/brand/citetrack-logo-${variant}.svg`}
      alt={alt}
      className={cn("shrink-0 select-none", className)}
      draggable={false}
      {...rest}
    />
  );
}
