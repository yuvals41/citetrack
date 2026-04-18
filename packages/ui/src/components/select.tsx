import * as Popover from "@radix-ui/react-popover";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ChevronDown, Search, X } from "lucide-react";
import { type KeyboardEvent, useId, useMemo, useRef, useState } from "react";
import { cn } from "./cn";
import { LoadingRows, OptionItem, SelectedPill } from "./select-internals";
import {
  buildRows,
  filterItems,
  flatOptions,
  type SelectGroup,
  type SelectItem,
  type SelectOption,
} from "./select-types";

// ─── Props types ──────────────────────────────────────────────────────────────

interface SelectBaseProps {
  /** Flat list of options or grouped option sets */
  options: SelectItem[];
  /** Placeholder shown in the trigger when no value is selected */
  placeholder?: string;
  /** Placeholder shown inside the search input (only used when `searchable`) */
  searchPlaceholder?: string;
  /** Message shown when no options match the query */
  emptyMessage?: string;
  disabled?: boolean;
  /** Show the search input in the dropdown. Defaults to `false`. */
  searchable?: boolean;
  /** Applies error styling to the trigger */
  error?: boolean;
  /**
   * When true, the dropdown body renders skeleton rows in place of options.
   * Use while options are being fetched asynchronously in the background.
   */
  isLoading?: boolean;
  /**
   * When true, the clear button is hidden so the user cannot deselect the
   * current value — only switch to another option. Use for fields where a
   * selection is mandatory (e.g. role pickers).
   */
  required?: boolean;
  className?: string;
}

interface SelectSingleProps extends SelectBaseProps {
  multiple?: false;
  value?: string;
  onValueChange?: (value: string) => void;
}

interface SelectMultipleProps extends SelectBaseProps {
  multiple: true;
  value?: string[];
  onValueChange?: (value: string[]) => void;
}

type SelectProps = SelectSingleProps | SelectMultipleProps;

// ─── Main component ───────────────────────────────────────────────────────────

function Select(props: SelectProps) {
  const {
    options,
    placeholder = "Select an option…",
    searchPlaceholder = "Search…",
    emptyMessage = "No options found.",
    disabled = false,
    searchable = false,
    error = false,
    isLoading = false,
    required = false,
    className,
  } = props;

  const isMultiple = props.multiple === true;

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeValue, setActiveValue] = useState<string | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  // Held in state (not a ref) so the virtualizer re-renders once the listbox
  // mounts inside Radix's Portal — a plain ref leaves the virtualizer with a
  // null scroll element on first paint and the dropdown looks empty.
  const [listEl, setListEl] = useState<HTMLDivElement | null>(null);
  const labelId = useId();

  const flat = useMemo(() => flatOptions(options), [options]);
  const filtered = useMemo(() => filterItems(options, query), [options, query]);
  const rows = useMemo(() => buildRows(filtered), [filtered]);
  const flatFiltered = useMemo(() => flatOptions(filtered).filter((o) => !o.disabled), [filtered]);

  const valueToRowIndex = useMemo(() => {
    const map = new Map<string, number>();
    for (const [idx, row] of rows.entries()) {
      if (row.kind === "option") {
        map.set(row.option.value, idx);
      }
    }
    return map;
  }, [rows]);

  const selectedValues: Set<string> = useMemo(() => {
    if (isMultiple) {
      return new Set((props as SelectMultipleProps).value ?? []);
    }
    const v = (props as SelectSingleProps).value;
    return v ? new Set([v]) : new Set();
  }, [isMultiple, props]);

  const selectedOptions = flat.filter((o) => selectedValues.has(o.value));

  // Always-on virtualizer. Estimated row height covers the common case
  // (single-line option ≈ 32px). Items with descriptions are auto-measured
  // via `measureElement` so they get their real heights after first paint.
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => listEl,
    estimateSize: () => 36,
    overscan: 8,
  });

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setQuery("");
      if (isMultiple) {
        setActiveValue(null);
      } else {
        setActiveValue((props as SelectSingleProps).value ?? null);
      }
      if (searchable && !isLoading) {
        requestAnimationFrame(() => searchRef.current?.focus());
      }
    }
  };

  const handleSelect = (val: string) => {
    if (isMultiple) {
      const cb = (props as SelectMultipleProps).onValueChange;
      const current = (props as SelectMultipleProps).value ?? [];
      if (current.includes(val)) {
        cb?.(current.filter((v) => v !== val));
      } else {
        cb?.([...current, val]);
      }
    } else {
      (props as SelectSingleProps).onValueChange?.(val);
      setOpen(false);
      setQuery("");
    }
  };

  const handleClear = () => {
    if (isMultiple) {
      (props as SelectMultipleProps).onValueChange?.([]);
    } else {
      (props as SelectSingleProps).onValueChange?.("");
    }
  };

  const handleRemove = (val: string) => {
    if (isMultiple) {
      const current = (props as SelectMultipleProps).value ?? [];
      (props as SelectMultipleProps).onValueChange?.(current.filter((v) => v !== val));
    }
  };

  const scrollActiveIntoView = (val: string) => {
    const idx = valueToRowIndex.get(val);
    if (idx !== undefined) {
      virtualizer.scrollToIndex(idx, { align: "auto" });
    }
  };

  const moveActive = (direction: 1 | -1) => {
    const currentIndex = flatFiltered.findIndex((o) => o.value === activeValue);
    const next =
      direction === 1
        ? (flatFiltered[currentIndex + 1] ?? flatFiltered[0])
        : (flatFiltered[currentIndex - 1] ?? flatFiltered[flatFiltered.length - 1]);
    if (next) {
      setActiveValue(next.value);
      scrollActiveIntoView(next.value);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      moveActive(1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      moveActive(-1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeValue) {
        handleSelect(activeValue);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const renderTriggerContent = () => {
    if (isMultiple) {
      if (selectedOptions.length === 0) {
        return <span className="truncate text-foreground-placeholder">{placeholder}</span>;
      }
      return (
        <span className="flex min-w-0 flex-wrap items-center gap-1">
          {selectedOptions.map((opt) => (
            <SelectedPill
              key={opt.value}
              label={opt.label}
              onRemove={() => handleRemove(opt.value)}
            />
          ))}
        </span>
      );
    }
    const singleSelected = selectedOptions[0];
    return (
      <span className={cn("truncate", !singleSelected && "text-foreground-placeholder")}>
        {singleSelected ? singleSelected.label : placeholder}
      </span>
    );
  };

  const renderListBody = () => {
    if (isLoading) {
      return <LoadingRows />;
    }
    if (rows.length === 0) {
      return <p className="py-4 text-center text-sm text-foreground-muted">{emptyMessage}</p>;
    }
    const virtualItems = virtualizer.getVirtualItems();
    return (
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualItems.map((virtualRow) => {
          const row = rows[virtualRow.index];
          if (!row) {
            return null;
          }
          return (
            <div
              key={row.key}
              data-index={virtualRow.index}
              ref={virtualizer.measureElement}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              {row.kind === "group-header" ? (
                <p className="px-2 py-1.5 text-xs font-semibold text-foreground-muted">
                  {row.label}
                </p>
              ) : (
                <OptionItem
                  option={row.option}
                  isSelected={selectedValues.has(row.option.value)}
                  isActive={activeValue === row.option.value}
                  onSelect={handleSelect}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const hasValue = selectedValues.size > 0;

  return (
    <Popover.Root open={open} onOpenChange={handleOpenChange}>
      <Popover.Trigger asChild>
        <button
          type="button"
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-labelledby={labelId}
          disabled={disabled}
          className={cn(
            "flex min-h-10 w-full cursor-pointer items-center justify-between rounded-sm border bg-background px-3 py-2 text-sm transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error ? "border-destructive" : "border-border",
            open && "ring-2 ring-ring ring-offset-1",
            className,
          )}
        >
          {renderTriggerContent()}
          <span className="ml-2 flex shrink-0 items-center gap-1">
            {hasValue && !isLoading && !required && (
              <button
                type="button"
                aria-label="Clear selection"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClear();
                }}
                className="flex h-4 w-4 cursor-pointer items-center justify-center rounded-full opacity-50 hover:opacity-100 focus:outline-none"
              >
                <X className="h-3 w-3" />
              </button>
            )}
            <ChevronDown
              className={cn(
                "h-4 w-4 opacity-50 transition-transform duration-200",
                open && "rotate-180",
              )}
            />
          </span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          sideOffset={4}
          align="start"
          onOpenAutoFocus={(e) => e.preventDefault()}
          className={cn(
            "z-50 w-(--radix-popover-trigger-width) min-w-48 overflow-hidden rounded-md border border-border bg-background text-foreground shadow-md",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
            "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
            "data-[side=bottom]:slide-in-from-top-2 data-[side=top]:slide-in-from-bottom-2",
          )}
        >
          {searchable && !isLoading && (
            <div className="flex items-center border-b border-border px-3">
              <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
              <input
                ref={searchRef}
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActiveValue(null);
                }}
                onKeyDown={handleKeyDown}
                placeholder={searchPlaceholder}
                aria-label="Search options"
                className="h-10 w-full bg-transparent py-2 text-sm outline-none placeholder:text-foreground-placeholder"
              />
              {query && (
                <button
                  type="button"
                  aria-label="Clear search"
                  onClick={() => {
                    setQuery("");
                    searchRef.current?.focus();
                  }}
                  className="ml-1 flex h-4 w-4 cursor-pointer items-center justify-center opacity-50 hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          )}

          <div
            ref={setListEl}
            role="listbox"
            aria-multiselectable={isMultiple || undefined}
            aria-label="Options"
            className="max-h-60 overflow-y-auto p-1"
          >
            {renderListBody()}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export type {
  SelectBaseProps,
  SelectGroup,
  SelectItem,
  SelectMultipleProps,
  SelectOption,
  SelectProps,
  SelectSingleProps,
};
export { Select };
