import { useAuth } from "@clerk/react";
import { useMutation } from "@tanstack/react-query";
import type {
  CrawlerSimInput,
  EntityAnalysisInput,
  ExtractabilityInput,
  QueryFanoutInput,
  ShoppingAnalysisInput,
} from "@citetrack/api-client";
import { createCitetrackClient } from "@citetrack/api-client";
import { newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function useAuthedClientFactory() {
  const { getToken } = useAuth();

  return () =>
    createCitetrackClient({
      baseUrl: BASE_URL,
      getToken,
      requestIdProvider: () => newRequestId(),
    });
}

export function useExtractabilityAnalyzer() {
  const createClient = useAuthedClientFactory();
  return useMutation({
    mutationFn: async (input: ExtractabilityInput) => createClient().runExtractability(input),
  });
}

export function useCrawlerSimAnalyzer() {
  const createClient = useAuthedClientFactory();
  return useMutation({
    mutationFn: async (input: CrawlerSimInput) => createClient().runCrawlerSim(input),
  });
}

export function useQueryFanoutAnalyzer() {
  const createClient = useAuthedClientFactory();
  return useMutation({
    mutationFn: async (input: QueryFanoutInput) => createClient().runQueryFanout(input),
  });
}

export function useEntityAnalysisAnalyzer() {
  const createClient = useAuthedClientFactory();
  return useMutation({
    mutationFn: async (input: EntityAnalysisInput) => createClient().runEntityAnalysis(input),
  });
}

export function useShoppingAnalysisAnalyzer() {
  const createClient = useAuthedClientFactory();
  return useMutation({
    mutationFn: async (input: ShoppingAnalysisInput) => createClient().runShoppingAnalysis(input),
  });
}
