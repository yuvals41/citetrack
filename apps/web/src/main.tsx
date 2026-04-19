import { ClerkProvider } from "@clerk/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { clerkAppearance } from "./lib/clerk-appearance";
import { queryClient, router } from "./router";
import "./styles.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (import.meta.env.PROD && !publishableKey) {
  throw new Error("Missing VITE_CLERK_PUBLISHABLE_KEY in production build.");
}

const root = document.getElementById("app");

if (!root) {
  throw new Error("Missing #app root element");
}

ReactDOM.createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      {publishableKey ? (
        <ClerkProvider publishableKey={publishableKey} appearance={clerkAppearance}>
          <RouterProvider router={router} />
        </ClerkProvider>
      ) : (
        <>
          <RouterProvider router={router} />
          <MissingClerkKeyBanner />
        </>
      )}
      {import.meta.env.DEV ? <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" /> : null}
    </QueryClientProvider>
  </StrictMode>,
);

function MissingClerkKeyBanner() {
  return (
    <div
      role="alert"
      className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md bg-foreground px-4 py-2 text-xs text-background shadow-md"
    >
      <strong className="font-semibold">Dev: Clerk not configured.</strong>{" "}
      Add <code>VITE_CLERK_PUBLISHABLE_KEY</code> to <code>apps/web/.env.local</code>.
    </div>
  );
}
