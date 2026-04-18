import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import type { ComponentPropsWithoutRef, HTMLAttributes } from "react";
import { cn } from "./cn";

const Drawer = DialogPrimitive.Root;
const DrawerTrigger = DialogPrimitive.Trigger;
const DrawerPortal = DialogPrimitive.Portal;
const DrawerClose = DialogPrimitive.Close;

/* ─── Overlay with keyframe fade ──────────────────────────────────────────── */

const overlayStyles = [
  "fixed inset-0 z-50 bg-black",
  // Radix sets data-state; use @keyframes so animation plays on mount/unmount
  "data-[state=open]:animate-[drawer-overlay-in_300ms_ease-out_forwards]",
  "data-[state=closed]:animate-[drawer-overlay-out_200ms_ease-in_forwards]",
].join(" ");

function DrawerOverlay({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>) {
  return <DialogPrimitive.Overlay className={cn(overlayStyles, className)} {...props} />;
}

/* ─── Content with keyframe slide ─────────────────────────────────────────── */

const drawerContentVariants = cva(
  ["fixed z-50 flex flex-col overflow-hidden border border-border bg-background shadow-xl"].join(
    " ",
  ),
  {
    variants: {
      side: {
        right: [
          "inset-y-0 right-0 h-full w-full max-w-md rounded-l-sm border-r-0",
          "data-[state=open]:animate-[drawer-in-right_300ms_cubic-bezier(0.32,0.72,0,1)_forwards]",
          "data-[state=closed]:animate-[drawer-out-right_200ms_ease-in_forwards]",
        ].join(" "),
        left: [
          "inset-y-0 left-0 h-full w-full max-w-md rounded-r-sm border-l-0",
          "data-[state=open]:animate-[drawer-in-left_300ms_cubic-bezier(0.32,0.72,0,1)_forwards]",
          "data-[state=closed]:animate-[drawer-out-left_200ms_ease-in_forwards]",
        ].join(" "),
        top: [
          "inset-x-0 top-0 h-auto w-full rounded-b-sm border-t-0",
          "data-[state=open]:animate-[drawer-in-top_300ms_cubic-bezier(0.32,0.72,0,1)_forwards]",
          "data-[state=closed]:animate-[drawer-out-top_200ms_ease-in_forwards]",
        ].join(" "),
        bottom: [
          "inset-x-0 bottom-0 h-auto w-full rounded-t-sm border-b-0",
          "data-[state=open]:animate-[drawer-in-bottom_300ms_cubic-bezier(0.32,0.72,0,1)_forwards]",
          "data-[state=closed]:animate-[drawer-out-bottom_200ms_ease-in_forwards]",
        ].join(" "),
      },
      size: {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-xl",
        xl: "max-w-2xl",
        full: "max-w-[100vw]",
      },
    },
    compoundVariants: [
      { side: ["top", "bottom"], size: "sm", className: "max-w-none max-h-[18rem]" },
      { side: ["top", "bottom"], size: "md", className: "max-w-none max-h-[24rem]" },
      { side: ["top", "bottom"], size: "lg", className: "max-w-none max-h-[32rem]" },
      { side: ["top", "bottom"], size: "xl", className: "max-w-none max-h-[40rem]" },
      { side: ["top", "bottom"], size: "full", className: "max-w-none max-h-[100vh]" },
    ],
    defaultVariants: {
      side: "right",
      size: "md",
    },
  },
);

interface DrawerContentProps
  extends ComponentPropsWithoutRef<typeof DialogPrimitive.Content>,
    VariantProps<typeof drawerContentVariants> {}

function DrawerContent({ className, children, side, size, ...props }: DrawerContentProps) {
  return (
    <DrawerPortal>
      <DrawerOverlay />
      <DialogPrimitive.Content
        className={cn(drawerContentVariants({ side, size }), className)}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute right-5 top-5 cursor-pointer rounded-sm p-1 opacity-60 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DrawerPortal>
  );
}

function DrawerHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-2 border-b border-border px-6 py-5 pr-14", className)}
      {...props}
    />
  );
}

function DrawerBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("min-h-0 flex-1 overflow-auto px-6 py-5", className)} {...props} />;
}

function DrawerFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-col-reverse gap-2 border-t border-border px-6 py-4 sm:flex-row sm:justify-end",
        className,
      )}
      {...props}
    />
  );
}

function DrawerTitle({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      className={cn("text-xl font-semibold leading-tight", className)}
      {...props}
    />
  );
}

function DrawerDescription({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      className={cn("text-sm text-foreground-muted", className)}
      {...props}
    />
  );
}

export type { DrawerContentProps };
export {
  Drawer,
  DrawerBody,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  DrawerPortal,
  DrawerTitle,
  DrawerTrigger,
};
