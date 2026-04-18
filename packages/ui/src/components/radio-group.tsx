import * as RadioGroupPrimitive from "@radix-ui/react-radio-group";
import { Circle } from "lucide-react";
import type { ComponentPropsWithoutRef, RefObject } from "react";
import { cn } from "./cn";

const RadioGroup = ({
  className,
  ref,
  ...props
}: ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Root> & {
  ref?: RefObject<HTMLDivElement | null>;
}) => <RadioGroupPrimitive.Root className={cn("grid gap-2", className)} {...props} ref={ref} />;

RadioGroup.displayName = "RadioGroup";

const RadioGroupItem = ({
  className,
  ref,
  ...props
}: ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Item> & {
  ref?: RefObject<HTMLButtonElement | null>;
}) => (
  <RadioGroupPrimitive.Item
    ref={ref}
    className={cn(
      "aspect-square h-5 w-5 cursor-pointer rounded-full border border-border bg-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-primary",
      className,
    )}
    {...props}
  >
    <RadioGroupPrimitive.Indicator className="flex items-center justify-center">
      <Circle className="h-2.5 w-2.5 fill-primary text-primary" />
    </RadioGroupPrimitive.Indicator>
  </RadioGroupPrimitive.Item>
);

RadioGroupItem.displayName = "RadioGroupItem";

export { RadioGroup, RadioGroupItem };
