import { AlertCircle, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";
import { Toaster as SonnerToaster, toast as sonnerToast } from "sonner";
import { cn } from "./cn";

// ─── Types ────────────────────────────────────────────────────────────────────

type ToastVariant = "default" | "success" | "warning" | "error" | "info";

type ToastPosition =
  | "bottom-right"
  | "bottom-left"
  | "bottom-center"
  | "top-right"
  | "top-left"
  | "top-center";

interface ToasterProps extends Omit<ComponentProps<typeof SonnerToaster>, "icons"> {
  position?: ToastPosition;
}

interface ToastOptions {
  description?: ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  cancel?: {
    label: string;
    onClick: () => void;
  };
  duration?: number;
  icon?: ReactNode | null;
  id?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  onAutoClose?: () => void;
  position?: ToastPosition;
}

// ─── Variant styles (matching the old visual design) ──────────────────────────

const variantStyles: Record<
  ToastVariant,
  { bg: string; border: string; text: string; iconColor: string }
> = {
  default: {
    bg: "var(--color-background, #fff)",
    border: "var(--color-border, #d4d4d4)",
    text: "var(--color-foreground, #0a0a0a)",
    iconColor: "var(--color-foreground-muted, #525252)",
  },
  success: {
    bg: "var(--color-success-bg, #f0fdf4)",
    border: "var(--color-success-border, #bbf7d0)",
    text: "var(--color-success-foreground, #166534)",
    iconColor: "var(--color-success, #166534)",
  },
  warning: {
    bg: "var(--color-warning-bg, #fffbeb)",
    border: "var(--color-warning-border, #fde68a)",
    text: "var(--color-warning-foreground, #92400e)",
    iconColor: "var(--color-warning, #92400e)",
  },
  error: {
    bg: "var(--color-error-bg, #fef2f2)",
    border: "var(--color-error-border, #fecaca)",
    text: "var(--color-error-foreground, #dc2626)",
    iconColor: "var(--color-destructive, #dc2626)",
  },
  info: {
    bg: "var(--color-info-bg, #eff6ff)",
    border: "var(--color-info-border, #bfdbfe)",
    text: "var(--color-info-foreground, #1e40af)",
    iconColor: "var(--color-info, #1e40af)",
  },
};

const variantIcons: Record<ToastVariant, ReactNode> = {
  default: (
    <Info
      className="h-5 w-5 shrink-0"
      style={{ color: "var(--color-foreground-muted, #525252)" }}
    />
  ),
  success: (
    <CheckCircle2 className="h-5 w-5 shrink-0" style={{ color: "var(--color-success, #166534)" }} />
  ),
  warning: (
    <AlertTriangle
      className="h-5 w-5 shrink-0"
      style={{ color: "var(--color-warning, #92400e)" }}
    />
  ),
  error: (
    <AlertCircle
      className="h-5 w-5 shrink-0"
      style={{ color: "var(--color-destructive, #dc2626)" }}
    />
  ),
  info: <Info className="h-5 w-5 shrink-0" style={{ color: "var(--color-info, #1e40af)" }} />,
};

// ─── Toaster (place once in your layout) ──────────────────────────────────────

function Toaster({ position = "bottom-right", className, ...props }: ToasterProps) {
  return (
    <SonnerToaster
      position={position}
      className={cn("toaster group", className)}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast:
            "group pointer-events-auto flex w-full items-start gap-3 rounded-sm border p-4 pr-8 shadow-lg font-sans",
          title: "text-sm font-semibold leading-tight",
          description: "text-sm opacity-90",
          actionButton:
            "inline-flex h-8 shrink-0 cursor-pointer items-center justify-center rounded-sm border px-3 text-sm font-medium transition-colors hover:opacity-80",
          cancelButton:
            "inline-flex h-8 shrink-0 cursor-pointer items-center justify-center rounded-sm border px-3 text-sm font-medium transition-colors opacity-70 hover:opacity-100",
          closeButton:
            "absolute right-2 top-2 rounded-sm p-0.5 opacity-50 transition-opacity hover:opacity-100",
        },
      }}
      {...props}
    />
  );
}

// ─── Toast helpers (imperative API matching Sonner) ───────────────────────────

function applyVariantStyle(variant: ToastVariant, options: ToastOptions) {
  const style = variantStyles[variant];
  const resolvedIcon = options.icon === null ? undefined : (options.icon ?? variantIcons[variant]);

  return {
    ...options,
    icon: resolvedIcon,
    style: {
      background: style.bg,
      border: `1px solid ${style.border}`,
      color: style.text,
      ...((typeof options === "object" && "style" in options
        ? (options as Record<string, unknown>)["style"]
        : {}) as Record<string, string>),
    },
  };
}

function toast(message: ReactNode, options?: ToastOptions) {
  return sonnerToast(message, applyVariantStyle("default", options ?? {}));
}

toast.success = (message: ReactNode, options?: ToastOptions) => {
  return sonnerToast(message, applyVariantStyle("success", options ?? {}));
};

toast.warning = (message: ReactNode, options?: ToastOptions) => {
  return sonnerToast(message, applyVariantStyle("warning", options ?? {}));
};

toast.error = (message: ReactNode, options?: ToastOptions) => {
  return sonnerToast(message, applyVariantStyle("error", options ?? {}));
};

toast.info = (message: ReactNode, options?: ToastOptions) => {
  return sonnerToast(message, applyVariantStyle("info", options ?? {}));
};

// Wrapped to avoid exposing Sonner's private PromiseIExtendedResult type (TS4032)
// biome-ignore lint/suspicious/noExplicitAny: sonner's promise result type is not exported
toast.promise = (...args: any[]) =>
  // biome-ignore lint/suspicious/noExplicitAny: sonner's promise result type is not exported
  (sonnerToast.promise as (...a: any[]) => any)(...args);
toast.loading = sonnerToast.loading;
toast.dismiss = sonnerToast.dismiss;

// ─── Exports ──────────────────────────────────────────────────────────────────

export type { ToasterProps, ToastOptions, ToastPosition, ToastVariant };
export { Toaster, toast };
