export const APP_NAME = "Citetrack AI" as const;
export const APP_URL = "https://citetrack.ai" as const;
export const API_BASE_URL =
  typeof process !== "undefined" && process.env?.API_BASE_URL
    ? process.env.API_BASE_URL
    : "http://localhost:8000";

export const AI_PROVIDERS = [
  "chatgpt",
  "claude",
  "perplexity",
  "gemini",
  "grok",
  "google_ai_overview",
] as const;

export type AIProvider = (typeof AI_PROVIDERS)[number];
