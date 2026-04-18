import type { WebhookEvent } from "@clerk/backend";
import { verifyWebhook } from "@clerk/backend/webhooks";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/api/webhooks/clerk")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        try {
          const event = await verifyWebhook(request);

          handleClerkWebhookEvent(event);

          // TODO Phase 3d: persist to backend via POST /api/v1/users/sync
          return Response.json({ received: true });
        } catch {
          return Response.json({ received: false, message: "Invalid webhook signature." }, { status: 400 });
        }
      },
    },
  },
});

function handleClerkWebhookEvent(event: WebhookEvent) {
  switch (event.type) {
    case "user.created":
    case "user.updated":
    case "user.deleted":
      console.info("[clerk:webhook] event received", {
        type: event.type,
        userId: event.data.id,
      });
      return;
    default:
      console.info("[clerk:webhook] ignored event", { type: event.type });
  }
}
