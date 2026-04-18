import { OTPInput, OTPInputContext } from "input-otp";
import { Minus } from "lucide-react";
import { type ComponentProps, type Ref, useContext } from "react";
import { cn } from "./cn";

// ─── Root ──────────────────────────────────────────────────────────────────

export type InputOTPProps = ComponentProps<typeof OTPInput> & {
  containerClassName?: string;
};

/**
 * Segmented input for one-time codes. Wraps the headless `input-otp` library
 * with project styling. Compose via `InputOTPGroup` + `InputOTPSlot`, e.g.:
 *
 * ```tsx
 * <InputOTP maxLength={6} value={code} onChange={setCode}>
 *   <InputOTPGroup>
 *     <InputOTPSlot index={0} />
 *     <InputOTPSlot index={1} />
 *     <InputOTPSlot index={2} />
 *     <InputOTPSeparator />
 *     <InputOTPSlot index={3} />
 *     <InputOTPSlot index={4} />
 *     <InputOTPSlot index={5} />
 *   </InputOTPGroup>
 * </InputOTP>
 * ```
 *
 * Uses `autocomplete="one-time-code"` by default so mobile browsers can
 * autofill codes from SMS / email notifications.
 */
function InputOTP({ className, containerClassName, ref, ...props }: InputOTPProps) {
  return (
    <OTPInput
      ref={ref}
      containerClassName={cn(
        "flex items-center gap-2 has-[:disabled]:opacity-50",
        containerClassName,
      )}
      className={cn("disabled:cursor-not-allowed", className)}
      autoComplete="one-time-code"
      {...props}
    />
  );
}

// ─── Group (visual cluster of slots) ──────────────────────────────────────

function InputOTPGroup({
  className,
  ref,
  ...props
}: ComponentProps<"div"> & { ref?: Ref<HTMLDivElement> }) {
  return <div ref={ref} className={cn("flex items-center gap-2", className)} {...props} />;
}

// ─── Slot ──────────────────────────────────────────────────────────────────

export type InputOTPSlotProps = ComponentProps<"div"> & {
  index: number;
  ref?: Ref<HTMLDivElement>;
};

function InputOTPSlot({ index, className, ref, ...props }: InputOTPSlotProps) {
  const ctx = useContext(OTPInputContext);
  const slot = ctx?.slots?.[index];
  const char = slot?.char ?? null;
  const hasFakeCaret = slot?.hasFakeCaret ?? false;
  const isActive = slot?.isActive ?? false;

  return (
    <div
      ref={ref}
      data-active={isActive ? "" : undefined}
      className={cn(
        // Base chrome — matches the project's input-like controls: dark
        // border, 4px radius, white background, tabular numerics.
        "relative flex h-12 w-10 items-center justify-center rounded-sm border border-foreground/20 bg-background text-lg font-medium tabular-nums text-foreground transition-all",
        // Active slot: highlighted ring + deeper border.
        "data-[active]:z-10 data-[active]:border-foreground data-[active]:shadow-[0_0_0_4px_rgba(0,0,0,0.06)]",
        className,
      )}
      {...props}
    >
      {char}
      {hasFakeCaret ? (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="h-5 w-px animate-pulse bg-foreground" />
        </div>
      ) : null}
    </div>
  );
}

// ─── Separator ─────────────────────────────────────────────────────────────

function InputOTPSeparator({
  ref,
  ...props
}: ComponentProps<"div"> & { ref?: Ref<HTMLDivElement> }) {
  // Purely decorative — the slots themselves carry the semantics.
  return (
    <div ref={ref} aria-hidden {...props}>
      <Minus className="h-4 w-4 text-foreground-muted" />
    </div>
  );
}

export { InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot };
