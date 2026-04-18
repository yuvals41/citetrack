import { type UIEvent, useCallback, useEffect, useRef, useState } from "react";
import { cn } from "./cn";

// ─── Types ────────────────────────────────────────────────────────────────────

interface TimePickerProps {
  /** Current value as "HH:mm" (24h) */
  value?: string;
  /** Called with "HH:mm" when user scrolls to a new time */
  onChange?: (time: string) => void;
  /** Use 12-hour format with AM/PM column */
  use12Hour?: boolean;
  /** Minute step: 1, 5, 10, 15, 30 */
  minuteStep?: number;
  disabled?: boolean;
  /** Minimum allowed hour (24h, inclusive). Hours before this are disabled. */
  minHour?: number;
  /** Minimum allowed minute (only applied when selected hour equals minHour). */
  minMinute?: number;
  className?: string;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const ITEM_H = 36;
const VISIBLE = 5;
const PAD_TOP = Math.floor(VISIBLE / 2) * ITEM_H;

function pad(n: number): string {
  return n.toString().padStart(2, "0");
}

function makeHours(is12: boolean): string[] {
  if (is12) {
    return Array.from({ length: 12 }, (_, i) => (i === 0 ? "12" : pad(i)));
  }
  return Array.from({ length: 24 }, (_, i) => pad(i));
}

function to24(h12: number, period: "AM" | "PM"): number {
  if (period === "AM" && h12 === 12) return 0;
  if (period === "PM" && h12 !== 12) return h12 + 12;
  return h12;
}

function buildDisabledHours(
  hours: string[],
  minHour: number | undefined,
  is12: boolean,
  period: "AM" | "PM",
): Set<string> | undefined {
  if (minHour == null) return undefined;
  const set = new Set<string>();
  for (const h of hours) {
    const h24 = is12 ? to24(Number.parseInt(h, 10), period) : Number.parseInt(h, 10);
    if (h24 < minHour) set.add(h);
  }
  return set.size > 0 ? set : undefined;
}

function buildDisabledMinutes(
  minutes: string[],
  minMinute: number | undefined,
): Set<string> | undefined {
  if (minMinute == null) return undefined;
  const set = new Set<string>();
  for (const m of minutes) {
    if (Number.parseInt(m, 10) < minMinute) set.add(m);
  }
  return set.size > 0 ? set : undefined;
}

function makeMinutes(step: number): string[] {
  const out: string[] = [];
  for (let i = 0; i < 60; i += step) {
    out.push(pad(i));
  }
  return out;
}

// ─── Scroll Column ───────────────────────────────────────────────────────────

interface ColProps {
  items: string[];
  selected: string;
  onSelect: (v: string) => void;
  disabled?: boolean;
  /** Set of item values that should appear disabled (grayed out, not clickable) */
  disabledItems?: Set<string>;
}

function Col({ items, selected, onSelect, disabled, disabledItems }: ColProps) {
  const ref = useRef<HTMLDivElement>(null);
  const busy = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // scroll to selected on mount / external change
  useEffect(() => {
    const idx = items.indexOf(selected);
    if (idx < 0 || !ref.current) {
      return;
    }
    busy.current = true;
    ref.current.scrollTo({ top: idx * ITEM_H, behavior: "smooth" });
    const t = setTimeout(() => {
      busy.current = false;
    }, 300);
    return () => clearTimeout(t);
  }, [selected, items]);

  // Trap wheel events so parent scroll containers don't steal them
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.stopPropagation();
    };
    el.addEventListener("wheel", onWheel);
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const onScroll = useCallback(
    (e: UIEvent<HTMLDivElement>) => {
      if (busy.current) {
        return;
      }
      if (timer.current) {
        clearTimeout(timer.current);
      }
      timer.current = setTimeout(() => {
        const el = e.target as HTMLDivElement;
        const idx = Math.round(el.scrollTop / ITEM_H);
        const clamped = Math.max(0, Math.min(idx, items.length - 1));
        const val = items[clamped];
        if (val && val !== selected) {
          onSelect(val);
        }
        busy.current = true;
        el.scrollTo({ top: clamped * ITEM_H, behavior: "smooth" });
        setTimeout(() => {
          busy.current = false;
        }, 200);
      }, 80);
    },
    [items, selected, onSelect],
  );

  const click = useCallback(
    (val: string, idx: number) => {
      if (disabled || disabledItems?.has(val)) {
        return;
      }
      onSelect(val);
      busy.current = true;
      ref.current?.scrollTo({ top: idx * ITEM_H, behavior: "smooth" });
      setTimeout(() => {
        busy.current = false;
      }, 300);
    },
    [disabled, disabledItems, onSelect],
  );

  return (
    <div
      ref={ref}
      onScroll={onScroll}
      className={cn(
        "w-14 overflow-y-auto scroll-smooth scrollbar-none",
        disabled && "pointer-events-none opacity-50",
      )}
      style={{ height: VISIBLE * ITEM_H }}
    >
      <div style={{ height: PAD_TOP }} />
      {items.map((item, i) => {
        const isItemDisabled = disabledItems?.has(item);
        return (
          <button
            key={item}
            type="button"
            onClick={() => click(item, i)}
            className={cn(
              "flex w-full items-center justify-center text-base tabular-nums transition-all duration-150",
              isItemDisabled
                ? "text-foreground-placeholder/30 pointer-events-none"
                : item === selected
                  ? "font-semibold text-foreground scale-110"
                  : "text-foreground-placeholder hover:text-foreground-muted",
            )}
            style={{ height: ITEM_H }}
          >
            {item}
          </button>
        );
      })}
      <div style={{ height: PAD_TOP }} />
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function TimePicker({
  value = "09:00",
  onChange,
  use12Hour = false,
  minuteStep = 1,
  disabled = false,
  minHour,
  minMinute,
  className,
}: TimePickerProps) {
  const hours = makeHours(use12Hour);
  const minutes = makeMinutes(minuteStep);

  const [rawH, rawM] = value.split(":");
  const ph = Number.parseInt(rawH ?? "9", 10);
  const pm = Number.parseInt(rawM ?? "0", 10);

  const initPeriod: "AM" | "PM" = ph >= 12 ? "PM" : "AM";
  const init12 = use12Hour ? (ph === 0 ? 12 : ph > 12 ? ph - 12 : ph) : ph;

  const [hour, setHour] = useState(use12Hour ? (init12 === 0 ? "12" : pad(init12)) : pad(ph));
  const [minute, setMinute] = useState(pad(pm));
  const [period, setPeriod] = useState<"AM" | "PM">(initPeriod);

  const emit = useCallback(
    (h: string, m: string, p: "AM" | "PM") => {
      let h24 = Number.parseInt(h, 10);
      if (use12Hour) {
        if (p === "AM" && h24 === 12) {
          h24 = 0;
        }
        if (p === "PM" && h24 !== 12) {
          h24 += 12;
        }
      }
      onChange?.(`${pad(h24)}:${m}`);
    },
    [use12Hour, onChange],
  );

  const onHour = useCallback(
    (h: string) => {
      setHour(h);
      emit(h, minute, period);
    },
    [minute, period, emit],
  );
  const onMinute = useCallback(
    (m: string) => {
      setMinute(m);
      emit(hour, m, period);
    },
    [hour, period, emit],
  );
  const onPeriod = useCallback(
    (p: "AM" | "PM") => {
      setPeriod(p);
      emit(hour, minute, p);
    },
    [hour, minute, emit],
  );

  const scrollH = VISIBLE * ITEM_H;

  // Compute disabled items based on minHour/minMinute
  const disabledHours = buildDisabledHours(hours, minHour, use12Hour, period);
  const selectedH24 = use12Hour
    ? to24(Number.parseInt(hour, 10), period)
    : Number.parseInt(hour, 10);
  const disabledMinutes =
    selectedH24 === minHour ? buildDisabledMinutes(minutes, minMinute) : undefined;

  return (
    <div
      className={cn(
        "inline-flex flex-col gap-2 rounded-sm border border-border bg-background p-4",
        disabled && "opacity-50",
        className,
      )}
    >
      {/* Labels row */}
      <div className="flex items-center gap-2">
        <div className="flex items-center">
          <span className="w-14 text-center text-[10px] font-medium uppercase tracking-widest text-foreground-muted">
            Hour
          </span>
          <span className="w-6" />
          <span className="w-14 text-center text-[10px] font-medium uppercase tracking-widest text-foreground-muted">
            Min
          </span>
        </div>
        {use12Hour && (
          <span className="w-12 text-center text-[10px] font-medium uppercase tracking-widest text-foreground-muted">
            &nbsp;
          </span>
        )}
      </div>

      {/* Scroll area with highlight band */}
      <div className="flex items-start gap-2">
        <div className="relative flex items-start">
          {/* Center highlight — only under the wheel area */}
          <div
            className="pointer-events-none absolute inset-x-0 rounded-sm bg-surface"
            style={{ top: PAD_TOP, height: ITEM_H }}
          />

          <Col
            items={hours}
            selected={hour}
            onSelect={onHour}
            disabled={disabled}
            disabledItems={disabledHours}
          />

          <div
            className="flex w-6 items-center justify-center text-base font-bold text-foreground-muted select-none"
            style={{ height: scrollH }}
          >
            :
          </div>

          <Col
            items={minutes}
            selected={minute}
            onSelect={onMinute}
            disabled={disabled}
            disabledItems={disabledMinutes}
          />
        </div>

        {use12Hour && (
          <div
            className="flex flex-col items-center justify-center gap-1"
            style={{ height: scrollH }}
          >
            {(["AM", "PM"] as const).map((p) => (
              <button
                key={p}
                type="button"
                disabled={disabled}
                onClick={() => onPeriod(p)}
                className={cn(
                  "flex h-9 w-12 cursor-pointer items-center justify-center rounded-sm text-xs font-semibold transition-colors",
                  period === p
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground-muted hover:bg-surface hover:text-foreground",
                )}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export type { TimePickerProps };
export { TimePicker };
