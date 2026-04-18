import * as Popover from "@radix-ui/react-popover";
import { CalendarIcon } from "lucide-react";
import { useCallback, useState } from "react";
import { Calendar } from "./calendar";
import { cn } from "./cn";
import { TimePicker } from "./time-picker";

interface DateTimePickerProps {
  /** Currently selected date + time. */
  value?: Date;
  /** Called when date or time changes. */
  onChange?: (date: Date) => void;
  /** Use 12-hour format with AM/PM column. */
  use12Hour?: boolean;
  /** Minute step for the time picker: 1, 5, 10, 15, 30. */
  minuteStep?: number;
  /** Disable all interaction. */
  disabled?: boolean;
  /** Earliest selectable date+time. Days before are disabled, hours/minutes on the boundary day are disabled. */
  minDate?: Date;
  className?: string;
}

function pad(n: number): string {
  return n.toString().padStart(2, "0");
}

function dateToTimeString(date: Date): string {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function DateTimePicker({
  value,
  onChange,
  use12Hour = false,
  minuteStep = 1,
  disabled = false,
  minDate,
  className,
}: DateTimePickerProps) {
  const [internalDate, setInternalDate] = useState<Date>(() => value ?? new Date());
  const current = value ?? internalDate;

  // Compute time constraints when selected day is the minDate day
  const isMinDay = minDate && isSameDay(current, minDate);
  const minHour = isMinDay ? minDate.getHours() : undefined;
  const minMinute = isMinDay ? minDate.getMinutes() : undefined;

  const handleDateSelect = useCallback(
    (day: Date | undefined) => {
      if (!day) {
        return;
      }
      const next = new Date(day);
      next.setHours(current.getHours(), current.getMinutes(), 0, 0);
      setInternalDate(next);
      onChange?.(next);
    },
    [current, onChange],
  );

  const handleTimeChange = useCallback(
    (time: string) => {
      const [h, m] = time.split(":");
      const next = new Date(current);
      next.setHours(Number.parseInt(h ?? "0", 10), Number.parseInt(m ?? "0", 10), 0, 0);
      setInternalDate(next);
      onChange?.(next);
    },
    [current, onChange],
  );

  return (
    <div
      className={cn(
        "inline-flex flex-col sm:flex-row rounded-sm border border-border bg-background",
        disabled && "opacity-50 pointer-events-none",
        className,
      )}
    >
      {/* Calendar */}
      <div>
        <Calendar
          mode="single"
          selected={current}
          onSelect={handleDateSelect}
          disableNavigation={disabled}
          disabled={minDate ? { before: minDate } : undefined}
          fromDate={minDate}
        />
      </div>

      {/* Separator */}
      <div className="h-px w-full shrink-0 sm:h-auto sm:w-px bg-border" />

      {/* Time picker — strip its own border/bg since we wrap it */}
      <TimePicker
        value={dateToTimeString(current)}
        onChange={handleTimeChange}
        use12Hour={use12Hour}
        minuteStep={minuteStep}
        disabled={disabled}
        minHour={minHour}
        minMinute={minMinute}
        className="border-0 bg-transparent"
      />
    </div>
  );
}

// ─── Trigger + popover variant ────────────────────────────────────────────────

interface DateTimePickerInputProps extends Omit<DateTimePickerProps, "className"> {
  /** Placeholder when no date is selected. */
  placeholder?: string;
  /** Format function for the trigger label. */
  formatDate?: (date: Date) => string;
  /** className applied to the trigger button. */
  className?: string;
}

const defaultFormat = (date: Date) => {
  const d = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const t = date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${d}  ${t}`;
};

function DateTimePickerInput({
  value,
  onChange,
  use12Hour = false,
  minuteStep = 1,
  disabled = false,
  minDate,
  placeholder = "Pick date & time",
  formatDate = defaultFormat,
  className,
}: DateTimePickerInputProps) {
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
          <DateTimePicker
            value={value}
            onChange={onChange}
            use12Hour={use12Hour}
            minuteStep={minuteStep}
            minDate={minDate}
            className="border-0"
          />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export type { DateTimePickerInputProps, DateTimePickerProps };
export { DateTimePicker, DateTimePickerInput };
