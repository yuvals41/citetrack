import { useAuth } from "@clerk/tanstack-react-start";
import { useQuery } from "@tanstack/react-query";
import { createCitetrackClient } from "@citetrack/api-client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function useSnapshotOverview(workspace = "default") {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "overview", workspace],
    queryFn: () => createCitetrackClient({ baseUrl: BASE_URL, getToken }).getSnapshotOverview(workspace),
    staleTime: 30_000,
  });
}

export function useSnapshotTrend(workspace = "default") {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "trend", workspace],
    queryFn: () => createCitetrackClient({ baseUrl: BASE_URL, getToken }).getSnapshotTrend(workspace),
    staleTime: 30_000,
  });
}

export function useSnapshotFindings(workspace = "default") {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "findings", workspace],
    queryFn: () => createCitetrackClient({ baseUrl: BASE_URL, getToken }).getSnapshotFindings(workspace),
    staleTime: 30_000,
  });
}

export function useSnapshotActions(workspace = "default") {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "actions", workspace],
    queryFn: () => createCitetrackClient({ baseUrl: BASE_URL, getToken }).getSnapshotActions(workspace),
    staleTime: 30_000,
  });
}
