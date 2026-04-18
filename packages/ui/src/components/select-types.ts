// Pure types and helpers for the Select component. Kept in a separate file
// so the main `select.tsx` can stay under the 400-line cap while still
// supporting virtualization, search filtering, and grouped options.

import type { ReactNode } from "react";

interface SelectOption {
  value: string;
  label: string;
  /** Optional secondary text rendered below the label */
  description?: string;
  disabled?: boolean;
  /** Content rendered at the trailing edge of the option row (e.g. status icons) */
  endContent?: ReactNode;
}

interface SelectGroup {
  label: string;
  options: SelectOption[];
}

type SelectItem = SelectOption | SelectGroup;

/**
 * A flattened display row consumed by the virtualizer. Group headers and
 * options share a single sequence so the virtualizer sees one homogeneous
 * list and `scrollToIndex` can target either kind directly.
 */
type SelectRow =
  | { kind: "group-header"; key: string; label: string }
  | { kind: "option"; key: string; option: SelectOption };

function isGroup(item: SelectItem): item is SelectGroup {
  return "options" in item;
}

function flatOptions(items: SelectItem[]): SelectOption[] {
  return items.flatMap((item) => (isGroup(item) ? item.options : [item]));
}

function filterItems(items: SelectItem[], query: string): SelectItem[] {
  const q = query.toLowerCase();
  if (!q) {
    return items;
  }
  return items.reduce<SelectItem[]>((acc, item) => {
    if (isGroup(item)) {
      const matched = item.options.filter(
        (o) => o.label.toLowerCase().includes(q) || o.description?.toLowerCase().includes(q),
      );
      if (matched.length > 0) {
        acc.push({ label: item.label, options: matched });
      }
    } else if (
      item.label.toLowerCase().includes(q) ||
      item.description?.toLowerCase().includes(q)
    ) {
      acc.push(item);
    }
    return acc;
  }, []);
}

function buildRows(items: SelectItem[]): SelectRow[] {
  const rows: SelectRow[] = [];
  for (const [i, item] of items.entries()) {
    if (isGroup(item)) {
      rows.push({ kind: "group-header", key: `g:${i}:${item.label}`, label: item.label });
      for (const opt of item.options) {
        rows.push({ kind: "option", key: `o:${opt.value}`, option: opt });
      }
    } else {
      rows.push({ kind: "option", key: `o:${item.value}`, option: item });
    }
  }
  return rows;
}

export type { SelectGroup, SelectItem, SelectOption, SelectRow };
export { buildRows, filterItems, flatOptions, isGroup };
