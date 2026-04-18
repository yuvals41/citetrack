import * as LabelPrimitive from "@radix-ui/react-label";
import type { ComponentPropsWithoutRef, Ref } from "react";
import { cn } from "./cn";

const Label = ({
  className,
  ref,
  ...props
}: ComponentPropsWithoutRef<typeof LabelPrimitive.Root> & {
  ref?: Ref<HTMLLabelElement>;
}) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(
      "cursor-pointer text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
      className,
    )}
    {...props}
  />
);

Label.displayName = "Label";

export { Label };
