import { Eye, EyeOff } from "lucide-react";
import { type InputHTMLAttributes, type Ref, useState } from "react";
import { cn } from "./cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  /**
   * Accessible label for the show-password toggle when `type="password"`.
   * @default "Show password"
   */
  showPasswordLabel?: string;
  /**
   * Accessible label for the hide-password toggle when `type="password"`.
   * @default "Hide password"
   */
  hidePasswordLabel?: string;
}

const Input = ({
  className,
  type,
  error,
  ref,
  showPasswordLabel = "Show password",
  hidePasswordLabel = "Hide password",
  ...props
}: InputProps & { ref?: Ref<HTMLInputElement> }) => {
  const [revealed, setRevealed] = useState(false);
  const isPassword = type === "password";
  const actualType = isPassword && revealed ? "text" : type;

  const inputEl = (
    <input
      type={actualType}
      className={cn(
        "flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-foreground-placeholder focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50",
        error ? "border-error focus-visible:ring-error" : "border-border focus-visible:ring-ring",
        isPassword && "pr-11",
        className,
      )}
      ref={ref}
      {...props}
    />
  );

  if (!isPassword) return inputEl;

  return (
    <div className="relative">
      {inputEl}
      <button
        type="button"
        onClick={() => setRevealed((v) => !v)}
        aria-label={revealed ? hidePasswordLabel : showPasswordLabel}
        aria-pressed={revealed}
        tabIndex={-1}
        className="absolute top-0 right-0 flex h-10 w-10 items-center justify-center text-foreground-muted transition-colors hover:text-foreground focus-visible:text-foreground focus-visible:outline-none"
      >
        {revealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
};

Input.displayName = "Input";

export type { InputProps };
export { Input };
