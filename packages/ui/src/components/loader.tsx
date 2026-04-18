import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "./cn";

const loaderVariants = cva(
  "animate-spin rounded-full border-2 border-current border-t-transparent",
  {
    variants: {
      size: {
        sm: "h-4 w-4",
        md: "h-6 w-6",
        lg: "h-8 w-8",
        xl: "h-12 w-12",
      },
      variant: {
        default: "text-foreground",
        muted: "text-foreground-muted",
        primary: "text-primary",
        white: "text-white",
      },
    },
    defaultVariants: {
      size: "md",
      variant: "default",
    },
  },
);

interface LoaderProps extends VariantProps<typeof loaderVariants> {
  className?: string;
  label?: string;
}

function Loader({ size, variant, className, label = "Loading..." }: LoaderProps) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn("inline-flex items-center gap-2", className)}
    >
      <span className={cn(loaderVariants({ size, variant }))} />
      <span className="sr-only">{label}</span>
    </span>
  );
}

export type { LoaderProps };
export { Loader, loaderVariants };
