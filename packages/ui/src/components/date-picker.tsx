import * as Popover from "@radix-ui/react-popover";
import { CalendarIcon } from "lucide-react";
import { useState } from "react";
import { Calendar } from "./calendar";
import { cn } from "./cn";

interface DatePickerProps {
  /** Currently selected date. */
  value?: Date;
  /** Called when a date is selected. */
  onChange?: (date: Date | undefined) => void;
  /** Placeholder when no date is selected. */
  placeholder?: string;
  /** Format function for displaying the date in the trigger. */
  formatDate?: (date: Date) => string;
  disabled?: boolean;
  className?: string;
}

const defaultFormat = (date: Date) =>
  date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

function DatePicker({
  value,
  onChange,
  placeholder = "Pick a date",
  formatDate = defaultFormat,
  disabled = false,
  className,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          disabled={disabled}
          className={cn(
            "inline-flex h-10 w-full items-center justify-between gap-2 rounded-sm border border-border bg-background px-3 text-sm transition-colors",
            "hover:bg-surface focus:outline-none focus:ring-2 focus:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50",
            !value && "text-foreground-placeholder",
            value && "text-foreground",
            className,
          )}
        >
          <span className="truncate">{value ? formatDate(value) : placeholder}</span>
          <CalendarIcon className="h-4 w-4 shrink-0 text-foreground-muted" />
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          sideOffset={6}
          align="start"
          className={cn(
            "z-50 rounded-sm border border-border bg-background shadow-lg",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
            "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
            "data-[side=bottom]:slide-in-from-top-2 data-[side=top]:slide-in-from-bottom-2",
          )}
        >
          <Calendar
            mode="single"
            selected={value}
            onSelect={(day) => {
              onChange?.(day);
              setOpen(false);
            }}
          />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export type { DatePickerProps };
export { DatePicker };
