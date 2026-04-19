import { ClerkProvider } from "@clerk/tanstack-react-start";
import { HeadContent, Scripts, createRootRoute } from "@tanstack/react-router";
import { TanStackDevtools } from "@tanstack/react-devtools";
import { TanStackRouterDevtoolsPanel } from "@tanstack/react-router-devtools";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { clerkAppearance } from "../lib/clerk-appearance";
import appCss from "../styles.css?url";

const queryClient = new QueryClient();

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Citetrack AI — Track how AI cites your brand" },
      {
        name: "description",
        content:
          "Monitor how your brand appears in ChatGPT, Claude, Perplexity, Gemini, Grok, and AI Overviews.",
      },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
      { rel: "alternate icon", href: "/favicon.ico" },
      { rel: "apple-touch-icon", href: "/favicon.svg" },
    ],
  }),
  shellComponent: RootDocument,
});

function RootDocument({ children }: { children: ReactNode }) {
  const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
  assertClerkConfiguredInProd(publishableKey);

  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body className="font-sans antialiased">
        <QueryClientProvider client={queryClient}>
          {publishableKey ? (
            <ClerkProvider publishableKey={publishableKey} appearance={clerkAppearance}>
              {children}
            </ClerkProvider>
          ) : (
            <>
              {children}
              <MissingClerkKeyBanner />
            </>
          )}
        </QueryClientProvider>
        {import.meta.env.DEV ? (
          <TanStackDevtools
            config={{ position: "bottom-right" }}
            plugins={[
              {
                name: "Tanstack Router",
                render: <TanStackRouterDevtoolsPanel />,
              },
            ]}
          />
        ) : null}
        <Scripts />
      </body>
    </html>
  );
}

function assertClerkConfiguredInProd(publishableKey: string | undefined): void {
  if (import.meta.env.PROD && !publishableKey) {
    throw new Error(
      "Missing VITE_CLERK_PUBLISHABLE_KEY in production build. " +
        "Set it in your hosting provider's environment before deploying.",
    );
  }
}

function MissingClerkKeyBanner() {
  return (
    <div
      role="alert"
      className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md bg-foreground px-4 py-2 text-xs text-background shadow-md"
    >
      <strong className="font-semibold">Dev: Clerk not configured.</strong>{" "}
      Add <code>VITE_CLERK_PUBLISHABLE_KEY</code> to <code>apps/web/.env.local</code> to enable
      auth.
    </div>
  );
}
