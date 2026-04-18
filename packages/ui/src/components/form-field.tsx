import type { ReactNode } from "react";
import { cn } from "./cn";
import { Label } from "./label";

interface SimpleFormFieldProps {
  label: string;
  error?: string;
  children: ReactNode;
  className?: string;
}

function SimpleFormField({ label, error, children, className }: SimpleFormFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label>{label}</Label>
      {children}
      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}
    </div>
  );
}
SimpleFormField.displayName = "SimpleFormField";

export type { SimpleFormFieldProps };
export { SimpleFormField };
