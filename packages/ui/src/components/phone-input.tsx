import * as PopoverPrimitive from "@radix-ui/react-popover";
import { Check, ChevronDown, Search } from "lucide-react";
import { type InputHTMLAttributes, useMemo, useRef, useState } from "react";
import { cn } from "./cn";
import { COUNTRIES, type Country, resolveCountry } from "./countries";

export type PhoneValue = {
  country: Country;
  number: string;
};

export interface PhoneInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange"> {
  /** Controlled value. */
  value: PhoneValue;
  /** Called with the full `{ country, number }` tuple on any change. */
  onChange: (value: PhoneValue) => void;
  /** Error state — reddens both the country button and the number input. */
  error?: boolean;
  /** Placeholder for the number field. @default "Phone number" */
  numberPlaceholder?: string;
  /** Accessible label for the country picker trigger. @default "Select country" */
  countryPickerLabel?: string;
  /** Placeholder for the search input inside the popover. @default "Search country" */
  searchPlaceholder?: string;
  /** Text shown when search has no results. @default "No country found" */
  emptyText?: string;
  /** `id` for the number `<input>` (use with `<label htmlFor>`). */
  id?: string;
  /** Forwarded to the number input for accessibility wiring. */
  "aria-invalid"?: boolean;
  /** Forwarded to the number input for accessibility wiring. */
  "aria-describedby"?: string;
}

/**
 * International phone number field with a searchable country/flag picker.
 *
 * Fully controlled — pass `{ country, number }` and an `onChange` handler.
 * The component makes **no network calls**: auto-detection of the user's
 * country by IP is the caller's responsibility (typically via a TanStack
 * Query) — pass the result as the initial `value.country`.
 */
export function PhoneInput({
  value,
  onChange,
  error,
  numberPlaceholder = "Phone number",
  countryPickerLabel = "Select country",
  searchPlaceholder = "Search country",
  emptyText = "No country found",
  className,
  id,
  disabled,
  onBlur,
  "aria-invalid": ariaInvalid,
  "aria-describedby": ariaDescribedBy,
  ...inputProps
}: PhoneInputProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return COUNTRIES;
    return COUNTRIES.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        c.dialCode.includes(q),
    );
  }, [query]);

  function handleNumberChange(e: React.ChangeEvent<HTMLInputElement>) {
    // Strip any non-digit characters — phone numbers are digits only.
    const digits = e.target.value.replace(/\D/g, "");
    onChange({ country: value.country, number: digits });
  }

  function handleCountrySelect(country: Country) {
    onChange({ country, number: value.number });
    setOpen(false);
    setQuery("");
  }

  const triggerStateClass = error
    ? "border-error shadow-[0_0_0_4px_rgba(220,38,38,0.08)]"
    : "border-foreground/20 hover:border-foreground/40";

  const inputStateClass = error
    ? "border-error shadow-[0_0_0_4px_rgba(220,38,38,0.08)]"
    : "border-foreground/20 focus-visible:border-foreground focus-visible:shadow-[0_0_0_4px_rgba(0,0,0,0.06)]";

  return (
    <div className={cn("flex gap-2", className)}>
      <PopoverPrimitive.Root
        open={open}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) setQuery("");
          // Focus the search input when the popover opens.
          if (next) setTimeout(() => searchRef.current?.focus(), 0);
        }}
      >
        <PopoverPrimitive.Trigger asChild>
          <button
            type="button"
            disabled={disabled}
            aria-label={countryPickerLabel}
            className={cn(
              "inline-flex h-10 shrink-0 items-center gap-2 rounded-md border bg-background px-3 text-sm transition-all focus-visible:outline-none focus-visible:border-foreground focus-visible:shadow-[0_0_0_4px_rgba(0,0,0,0.06)] disabled:cursor-not-allowed disabled:opacity-50",
              triggerStateClass,
            )}
          >
            <ChevronDown className="h-3.5 w-3.5 opacity-60" aria-hidden />
            <span className="text-lg leading-none" aria-hidden>
              {value.country.flag}
            </span>
            <span className="font-medium tabular-nums">{value.country.dialCode}</span>
          </button>
        </PopoverPrimitive.Trigger>
        <PopoverPrimitive.Portal>
          <PopoverPrimitive.Content
            align="start"
            sideOffset={6}
            className="z-50 w-72 overflow-hidden rounded-md border border-foreground/20 bg-background shadow-lg outline-none"
          >
            <div className="flex items-center gap-2 border-b border-foreground/10 px-3">
              <Search className="h-4 w-4 shrink-0 text-foreground-muted" aria-hidden />
              <input
                ref={searchRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={searchPlaceholder}
                className="h-10 w-full bg-transparent text-sm outline-none placeholder:text-foreground-placeholder"
                aria-label={searchPlaceholder}
              />
            </div>
            {/* biome-ignore lint/a11y/noNoninteractiveElementToInteractiveRole: listbox on ul is the correct ARIA pattern for a custom combobox listbox */}
            <ul className="max-h-64 overflow-y-auto py-1" role="listbox">
              {filtered.length === 0 ? (
                <li
                  className="px-3 py-6 text-center text-xs text-foreground-muted"
                  role="presentation"
                >
                  {emptyText}
                </li>
              ) : (
                filtered.map((c) => {
                  const selected = c.code === value.country.code;
                  return (
                    <li key={c.code} role="presentation">
                      <button
                        type="button"
                        onClick={() => handleCountrySelect(c)}
                        role="option"
                        aria-selected={selected}
                        className={cn(
                          "flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-surface focus-visible:bg-surface focus-visible:outline-none",
                          selected && "bg-surface",
                        )}
                      >
                        <span className="text-lg leading-none" aria-hidden>
                          {c.flag}
                        </span>
                        <span className="flex-1 truncate">{c.name}</span>
                        <span className="text-xs tabular-nums text-foreground-muted">
                          {c.dialCode}
                        </span>
                        {selected ? (
                          <Check className="h-4 w-4 text-foreground" aria-hidden />
                        ) : null}
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
          </PopoverPrimitive.Content>
        </PopoverPrimitive.Portal>
      </PopoverPrimitive.Root>

      <input
        {...inputProps}
        id={id}
        type="tel"
        inputMode="numeric"
        autoComplete="tel-national"
        disabled={disabled}
        value={value.number}
        onChange={handleNumberChange}
        onBlur={onBlur}
        placeholder={numberPlaceholder}
        aria-invalid={ariaInvalid}
        aria-describedby={ariaDescribedBy}
        className={cn(
          "flex h-10 w-full rounded-md border bg-background px-3 text-sm transition-all focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 placeholder:text-foreground-placeholder",
          inputStateClass,
        )}
      />
    </div>
  );
}

/**
 * Convenience factory — returns a `PhoneValue` with a resolved country and
 * an empty number. Handy for building default form values from an ISO code.
 */
export function createPhoneValue(countryCode: string | null | undefined, number = ""): PhoneValue {
  return { country: resolveCountry(countryCode), number };
}
