import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SearchOut } from "@/types";

export function useSearch(q: string) {
  return useQuery<SearchOut>({
    queryKey: ["search", q],
    queryFn: () => api.get("/search", { params: { q } }).then((r) => r.data),
    enabled: q.trim().length >= 2,
    staleTime: 10_000,
  });
}
