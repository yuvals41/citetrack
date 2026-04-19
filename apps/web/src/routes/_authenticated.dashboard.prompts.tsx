import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/prompts")({
  component: () => (
    <PlaceholderPage
      title="Prompts"
      description="The prompts we run against ChatGPT, Claude, Perplexity, Gemini, and Grok to measure visibility."
    />
  ),
});
