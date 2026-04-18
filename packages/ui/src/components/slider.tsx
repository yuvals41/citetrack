import * as SliderPrimitive from "@radix-ui/react-slider";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { type ComponentPropsWithoutRef, useCallback, useState } from "react";
import { cn } from "./cn";

type SliderProps = ComponentPropsWithoutRef<typeof SliderPrimitive.Root> & {
  /** Show a tooltip with the current value when hovering or dragging a thumb. */
  showTooltip?: boolean;
};

function Slider({ className, showTooltip = false, onValueChange, ...props }: SliderProps) {
  const defaultValues = props.value ?? props.defaultValue ?? [0];
  const [internalValues, setInternalValues] = useState<number[]>(defaultValues);

  const handleValueChange = useCallback(
    (newValue: number[]) => {
      setInternalValues(newValue);
      onValueChange?.(newValue);
    },
    [onValueChange],
  );

  const displayValues = props.value ?? internalValues;

  return (
    <TooltipPrimitive.Provider delayDuration={0}>
      <SliderPrimitive.Root
        className={cn("relative flex w-full touch-none select-none items-center", className)}
        onValueChange={handleValueChange}
        {...props}
      >
        <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-surface">
          <SliderPrimitive.Range className="absolute h-full bg-primary" />
        </SliderPrimitive.Track>
        {displayValues.map((val, i) => (
          <ThumbWithTooltip
            // biome-ignore lint/suspicious/noArrayIndexKey: slider thumbs have no stable identity; index is correct here
            key={i}
            value={val}
            showTooltip={showTooltip}
          />
        ))}
      </SliderPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}

const thumbClassName =
  "block h-4 w-4 cursor-pointer rounded-full border-2 border-primary bg-background shadow transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";

function ThumbWithTooltip({ value, showTooltip }: { value: number; showTooltip: boolean }) {
  const [hovered, setHovered] = useState(false);
  const [dragging, setDragging] = useState(false);

  const handlePointerDown = useCallback(() => {
    setDragging(true);
    const handlePointerUp = () => {
      setDragging(false);
      document.removeEventListener("pointerup", handlePointerUp);
    };
    document.addEventListener("pointerup", handlePointerUp);
  }, []);

  if (!showTooltip) {
    return <SliderPrimitive.Thumb className={thumbClassName} />;
  }

  return (
    <TooltipPrimitive.Root open={hovered || dragging}>
      <TooltipPrimitive.Trigger asChild>
        <SliderPrimitive.Thumb
          className={thumbClassName}
          onPointerEnter={() => setHovered(true)}
          onPointerLeave={() => setHovered(false)}
          onPointerDown={handlePointerDown}
        />
      </TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          side="top"
          sideOffset={6}
          className={cn(
            "z-50 overflow-visible rounded-sm bg-foreground px-3 py-1.5 text-xs text-background shadow-md",
            "animate-in fade-in-0 zoom-in-95",
            "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
            "data-[side=bottom]:slide-in-from-top-2 data-[side=top]:slide-in-from-bottom-2",
          )}
        >
          {value}
          <TooltipPrimitive.Arrow className="fill-foreground" width={10} height={5} />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}

export type { SliderProps };
export { Slider };
