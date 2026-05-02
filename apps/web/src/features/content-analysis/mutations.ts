import type {
  CrawlerSimInput,
  EntityAnalysisInput,
  ExtractabilityInput,
  QueryFanoutInput,
  ShoppingAnalysisInput,
} from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useMutation } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { newRequestId } from "#/lib/logger";

function useAuthedRequest() {
  const { getToken } = useAuth();

  return async <TInput, TOutput>(
    input: TInput,
    runner: (client: ReturnType<typeof buildClient>, value: TInput) => Promise<TOutput>,
  ) => {
    const requestId = newRequestId();
    return runner(buildClient(getToken, requestId), input);
  };
}

export function useExtractabilityAnalyzer() {
  const run = useAuthedRequest();
  return useMutation({
    mutationFn: async (input: ExtractabilityInput) =>
      run(input, (client, value) => client.runExtractability(value)),
  });
}

export function useCrawlerSimAnalyzer() {
  const run = useAuthedRequest();
  return useMutation({
    mutationFn: async (input: CrawlerSimInput) =>
      run(input, (client, value) => client.runCrawlerSim(value)),
  });
}

export function useQueryFanoutAnalyzer() {
  const run = useAuthedRequest();
  return useMutation({
    mutationFn: async (input: QueryFanoutInput) =>
      run(input, (client, value) => client.runQueryFanout(value)),
  });
}

export function useEntityAnalysisAnalyzer() {
  const run = useAuthedRequest();
  return useMutation({
    mutationFn: async (input: EntityAnalysisInput) =>
      run(input, (client, value) => client.runEntityAnalysis(value)),
  });
}

export function useShoppingAnalysisAnalyzer() {
  const run = useAuthedRequest();
  return useMutation({
    mutationFn: async (input: ShoppingAnalysisInput) =>
      run(input, (client, value) => client.runShoppingAnalysis(value)),
  });
}
