import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Stats } from "@/types";

export function useStats() {
  return useQuery<Stats>({
    queryKey: ["stats"],
    queryFn: () => api.get("/stats").then((r) => r.data),
    refetchInterval: 60_000,
  });
}
