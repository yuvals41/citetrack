import type { Ref, TextareaHTMLAttributes } from "react";
import { cn } from "./cn";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

const Textarea = ({
  className,
  error,
  ref,
  ...props
}: TextareaProps & { ref?: Ref<HTMLTextAreaElement> }) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[80px] rounded-md border bg-background px-3 py-2 text-sm transition-colors placeholder:text-foreground-placeholder focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50",
        error ? "border-error focus-visible:ring-error" : "border-border focus-visible:ring-ring",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
};

Textarea.displayName = "Textarea";

export type { TextareaProps };
export { Textarea };
