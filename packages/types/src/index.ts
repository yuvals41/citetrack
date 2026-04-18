import type { AIProvider } from "@citetrack/config";

export type Workspace = {
  id: string;
  slug: string;
  brandName: string;
  domain: string;
  createdAt: string;
};

export type VisibilityScore = {
  provider: AIProvider;
  score: number;
  mentions: number;
  citations: number;
};

export type ScanRun = {
  id: string;
  workspaceId: string;
  status: "pending" | "running" | "completed" | "completed_with_partial_failures" | "failed";
  startedAt: string;
  completedAt: string | null;
  providers: AIProvider[];
};

export type Citation = {
  url: string;
  domain: string;
  provider: AIProvider;
  context: string;
};

export type DiagnosticFinding = {
  reasonCode: string;
  severity: "high" | "medium" | "low";
  provider: AIProvider | null;
  message: string;
  fix: string;
};

export type { AIProvider };
