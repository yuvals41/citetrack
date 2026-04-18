import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes, KeyboardEvent } from "react";
import { cn } from "./cn";

const tagVariants = cva(
  "inline-flex items-center gap-1 rounded-sm border px-2 py-0.5 text-xs font-medium leading-tight transition-colors",
  {
    variants: {
      variant: {
        default: "border-border bg-surface text-foreground",
        solid: "border-primary bg-primary text-primary-foreground",
        outline: "border-border-strong bg-background text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

interface TagProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof tagVariants> {
  onRemove?: () => void;
  removable?: boolean;
}

function Tag({ variant, onRemove, removable = false, className, children, ...props }: TagProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onRemove?.();
    }
  };

  return (
    <span className={cn(tagVariants({ variant }), className)} {...props}>
      {children}
      {(removable || onRemove) && (
        <button
          type="button"
          aria-label="Remove tag"
          onClick={onRemove}
          onKeyDown={handleKeyDown}
          className="ml-0.5 -mr-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full opacity-60 transition-opacity hover:opacity-100 focus:outline-none focus:ring-1 focus:ring-current"
        >
          <svg width="8" height="8" viewBox="0 0 8 8" fill="none" aria-hidden="true">
            <path
              d="M1.5 1.5l5 5M6.5 1.5l-5 5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}
    </span>
  );
}

/** TagGroup — renders a collection of tags with a shared onRemove handler */
interface TagGroupProps extends HTMLAttributes<HTMLDivElement> {
  tags: string[];
  variant?: TagProps["variant"];
  onRemove?: (tag: string, index: number) => void;
}

function TagGroup({ tags, variant, onRemove, className, ...props }: TagGroupProps) {
  return (
    <div className={cn("flex flex-wrap gap-1.5", className)} {...props}>
      {tags.map((tag, i) => (
        <Tag
          key={tag}
          variant={variant}
          removable={!!onRemove}
          onRemove={onRemove ? () => onRemove(tag, i) : undefined}
        >
          {tag}
        </Tag>
      ))}
    </div>
  );
}

export type { TagGroupProps, TagProps };
export { Tag, TagGroup, tagVariants };
