import * as Popover from "@radix-ui/react-popover";
import { useState } from "react";
import { HexColorPicker } from "react-colorful";
import { cn } from "./cn";

export interface ColorPickerProps {
  /** Current hex color value (e.g. "#ff0000"). */
  value: string;
  /** Called when the color changes. */
  onChange: (value: string) => void;
  /** Called when the picker loses focus. */
  onBlur?: () => void;
  disabled?: boolean;
  className?: string;
}

function ColorPicker({ value, onChange, onBlur, disabled = false, className }: ColorPickerProps) {
  const [open, setOpen] = useState(false);
  const displayValue = value || "#ffffff";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Popover.Root open={open} onOpenChange={setOpen}>
        <Popover.Trigger asChild disabled={disabled}>
          <button
            type="button"
            onBlur={onBlur}
            className={cn(
              "h-10 w-10 shrink-0 cursor-pointer rounded-sm border border-border transition-colors",
              "hover:ring-2 hover:ring-ring focus:outline-none focus:ring-2 focus:ring-ring",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
            style={{ backgroundColor: displayValue }}
            aria-label={`Pick color, current: ${displayValue}`}
          />
        </Popover.Trigger>

        <Popover.Portal>
          <Popover.Content
            className="z-50 rounded-lg border border-border bg-background p-3 shadow-lg"
            sideOffset={8}
            align="start"
          >
            <div className="flex flex-col gap-3">
              <HexColorPicker color={displayValue} onChange={onChange} />
              <input
                type="text"
                value={displayValue}
                onChange={(e) => {
                  const v = e.target.value;
                  if (/^#[0-9a-fA-F]{0,6}$/.test(v) || v === "#") {
                    onChange(v);
                  }
                }}
                maxLength={7}
                className={cn(
                  "h-9 w-full rounded-sm border border-border bg-background px-3 font-mono text-sm",
                  "focus:outline-none focus:ring-2 focus:ring-ring",
                )}
              />
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>

      <span className="select-none font-mono text-sm text-foreground-muted">{displayValue}</span>
    </div>
  );
}

export { ColorPicker };
