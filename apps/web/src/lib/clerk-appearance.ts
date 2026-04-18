import { ClerkProvider } from "@clerk/tanstack-react-start";
import type { ComponentProps } from "react";

type ClerkAppearance = NonNullable<ComponentProps<typeof ClerkProvider>["appearance"]>;

export const clerkAppearance: ClerkAppearance = {
  variables: {
    colorPrimary: "#0a0a0a",
    colorBackground: "#ffffff",
    colorText: "#0a0a0a",
    colorTextSecondary: "#71717a",
    colorInputBackground: "#ffffff",
    colorInputText: "#0a0a0a",
    borderRadius: "0.5rem",
    fontFamily: '"Inter", system-ui, sans-serif',
  },
  elements: {
    card: "shadow-none ring-1 ring-foreground/10 rounded-xl",
    headerTitle: "font-medium text-lg",
    headerSubtitle: "text-sm text-muted-foreground",
    formButtonPrimary:
      "bg-foreground text-background hover:bg-foreground/90 rounded-md font-medium shadow-none",
    formFieldInput: "rounded-md border border-border bg-background text-foreground",
    footerActionLink: "text-foreground hover:underline",
    socialButtonsBlockButton: "ring-1 ring-foreground/10 hover:bg-muted rounded-md shadow-none",
    dividerLine: "bg-border",
    dividerText: "text-muted-foreground text-xs",
  },
};
