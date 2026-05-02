import { createFileRoute } from "@tanstack/react-router";
import { ContentAnalysisPage } from "#/features/content-analysis/content-analysis-page";

export const Route = createFileRoute("/_authenticated/dashboard/content-analysis")({
  component: ContentAnalysisPage,
});
