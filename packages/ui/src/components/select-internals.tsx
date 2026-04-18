// Internal sub-components for `select.tsx`. Split out to keep the main file
// under the 400-line cap. These are not exported from the package — only
// `select.tsx` consumes them.

import { X } from "lucide-react";
import { cn } from "./cn";
import type { SelectOption } from "./select-types";
import { Skeleton } from "./skeleton";

interface OptionItemProps {
  option: SelectOption;
  isSelected: boolean;
  isActive: boolean;
  onSelect: (value: string) => void;
}

function OptionItem({ option, isSelected, isActive, onSelect }: OptionItemProps) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={isSelected}
      aria-disabled={option.disabled}
      disabled={option.disabled}
      onClick={() => onSelect(option.value)}
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center gap-3 rounded-sm px-2 py-1.5 text-left text-sm outline-none transition-colors hover:bg-surface",
        isActive && "bg-surface",
        option.disabled && "pointer-events-none opacity-50",
        isSelected && !isActive && "bg-surface/60",
      )}
    >
      <span className="flex flex-col gap-0.5 min-w-0">
        <span className="truncate leading-snug">{option.label}</span>
        {option.description && (
          <span className="truncate text-xs text-foreground-muted leading-snug">
            {option.description}
          </span>
        )}
      </span>
      {option.endContent && <span className="ml-auto shrink-0">{option.endContent}</span>}
    </button>
  );
}

function SelectedPill({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-0.5 rounded-sm border border-border bg-surface px-1.5 py-0.5 text-xs leading-tight">
      <span className="truncate max-w-32">{label}</span>
      <button
        type="button"
        aria-label={`Remove ${label}`}
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="ml-0.5 flex h-3 w-3 shrink-0 cursor-pointer items-center justify-center rounded-full opacity-50 hover:opacity-100 focus:outline-none"
      >
        <X className="h-2.5 w-2.5" />
      </button>
    </span>
  );
}

const LOADING_ROWS = [
  { id: "ls-1", w: "w-3/4" },
  { id: "ls-2", w: "w-2/3" },
  { id: "ls-3", w: "w-5/6" },
  { id: "ls-4", w: "w-1/2" },
  { id: "ls-5", w: "w-3/5" },
];

function LoadingRows() {
  return (
    <div aria-busy="true" aria-live="polite" className="flex flex-col gap-1 p-1">
      {LOADING_ROWS.map((row) => (
        <div key={row.id} className="flex items-center gap-3 rounded-sm px-2 py-1.5">
          <Skeleton className={cn("h-3.5", row.w)} />
        </div>
      ))}
    </div>
  );
}

export { LoadingRows, OptionItem, SelectedPill };
