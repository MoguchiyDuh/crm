import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProjectPriority, ProjectStatus } from "@/types";

export function useStatuses() {
  return useQuery<ProjectStatus[]>({
    queryKey: ["statuses"],
    queryFn: () => api.get("/reference/statuses").then((r) => r.data),
    staleTime: 1000 * 60 * 10,
  });
}

export function usePriorities() {
  return useQuery<ProjectPriority[]>({
    queryKey: ["priorities"],
    queryFn: () => api.get("/reference/priorities").then((r) => r.data),
    staleTime: 1000 * 60 * 10,
  });
}
