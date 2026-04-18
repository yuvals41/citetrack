import { Eye, EyeOff } from "lucide-react";
import { type InputHTMLAttributes, type RefObject, useState } from "react";
import { cn } from "./cn";

interface FloatingInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
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

function FloatingInput({
  label,
  className,
  type,
  error,
  id,
  value,
  defaultValue,
  onFocus,
  onBlur,
  ref,
  showPasswordLabel = "Show password",
  hidePasswordLabel = "Hide password",
  ...props
}: FloatingInputProps & { ref?: RefObject<HTMLInputElement | null> }) {
  const [focused, setFocused] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const hasValue = value === undefined ? false : String(value).length > 0;
  const [filled, setFilled] = useState(!!defaultValue);
  const isActive = focused || hasValue || filled;
  const isPassword = type === "password";
  const actualType = isPassword && revealed ? "text" : type;

  function handleFocus(e: React.FocusEvent<HTMLInputElement>) {
    setFocused(true);
    onFocus?.(e);
  }

  function handleBlur(e: React.FocusEvent<HTMLInputElement>) {
    setFocused(false);
    setFilled(e.target.value.length > 0);
    onBlur?.(e);
  }

  return (
    <div className="relative">
      <input
        type={actualType}
        id={id}
        ref={ref}
        value={value}
        defaultValue={defaultValue}
        className={cn(
          "peer flex h-10 w-full rounded-md border bg-background text-sm leading-none caret-foreground transition-all focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50",
          "px-3 py-0",
          error
            ? "border-error shadow-[0_0_0_4px_rgba(220,38,38,0.08)]"
            : focused
              ? "border-foreground shadow-[0_0_0_4px_rgba(0,0,0,0.06)]"
              : "border-foreground/20",
          isPassword && "pr-11",
          className,
        )}
        placeholder=" "
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...props}
      />
      <label
        htmlFor={id}
        className={cn(
          "pointer-events-none absolute left-3 transition-all duration-200 ease-out",
          isActive
            ? "top-px -translate-y-1/2 bg-background px-1 text-xs font-medium"
            : "top-1/2 -translate-y-1/2 text-sm",
          error
            ? "text-error-foreground"
            : isActive
              ? "text-foreground"
              : "text-foreground-placeholder",
        )}
      >
        {label}
      </label>
      {isPassword && (
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
      )}
    </div>
  );
}

export type { FloatingInputProps };
export { FloatingInput };
