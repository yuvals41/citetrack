import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import type { ComponentPropsWithoutRef, HTMLAttributes } from "react";
import { cn } from "./cn";
import { OVERLAY_CLASS } from "./overlay";

const Modal = DialogPrimitive.Root;
const ModalTrigger = DialogPrimitive.Trigger;
const ModalPortal = DialogPrimitive.Portal;
const ModalClose = DialogPrimitive.Close;

function ModalOverlay({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>) {
  return <DialogPrimitive.Overlay className={cn(OVERLAY_CLASS, className)} {...props} />;
}

const modalContentVariants = cva(
  [
    "fixed left-1/2 top-1/2 z-50 flex w-[calc(100vw-2rem)] flex-col",
    "overflow-hidden border border-border bg-background shadow-xl rounded-sm",
    "data-[state=open]:animate-[dialog-content-in_150ms_ease-out_forwards]",
    "data-[state=closed]:animate-[dialog-content-out_100ms_ease-in_forwards]",
  ].join(" "),
  {
    variants: {
      size: {
        sm: "max-w-md",
        md: "max-w-2xl",
        lg: "max-w-4xl",
        xl: "max-w-6xl",
        full: "h-[calc(100vh-2rem)] max-w-[calc(100vw-2rem)]",
      },
    },
    defaultVariants: {
      size: "md",
    },
  },
);

interface ModalContentProps
  extends ComponentPropsWithoutRef<typeof DialogPrimitive.Content>,
    VariantProps<typeof modalContentVariants> {}

function ModalContent({ className, children, size, ...props }: ModalContentProps) {
  return (
    <ModalPortal>
      <ModalOverlay />
      <DialogPrimitive.Content className={cn(modalContentVariants({ size }), className)} {...props}>
        {children}
        <DialogPrimitive.Close className="absolute right-5 top-5 cursor-pointer rounded-sm p-1 opacity-60 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </ModalPortal>
  );
}

function ModalHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-2 border-b border-border px-6 py-5 pr-14", className)}
      {...props}
    />
  );
}

function ModalBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-6 py-5", className)} {...props} />;
}

function ModalFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
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

function ModalTitle({
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

function ModalDescription({
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

export type { ModalContentProps };
export {
  Modal,
  ModalBody,
  ModalClose,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalPortal,
  ModalTitle,
  ModalTrigger,
};
