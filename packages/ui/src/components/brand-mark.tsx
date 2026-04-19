import type { SVGProps } from "react";
import { cn } from "./cn";

/** Citetrack brand mark — inline SVG that mirrors the favicon. Prefer over `<img>` to avoid 404s and keep brand/favicon in sync. */
export function BrandMark({
  className,
  title = "Citetrack AI",
  ...rest
}: SVGProps<SVGSVGElement> & { title?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      role="img"
      aria-label={title}
      className={cn("shrink-0", className)}
      xmlns="http://www.w3.org/2000/svg"
      {...rest}
    >
      <title>{title}</title>
      <rect width="32" height="32" rx="7" fill="#0a0a0a" />
      <path d="M8 9 h5 v6 l-3 7 h-3 v-6 z" fill="#fafafa" />
      <path d="M18 9 h5 v6 l-3 7 h-3 v-6 z" fill="#fafafa" />
    </svg>
  );
}
