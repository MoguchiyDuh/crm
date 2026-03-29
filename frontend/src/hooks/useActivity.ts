import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ActivityLog } from "@/types";

interface ActivityFilters {
  limit?: number;
  offset?: number;
  entity_type?: string;
}

export function useActivity(filters: ActivityFilters = {}) {
  return useQuery<ActivityLog[]>({
    queryKey: ["activity", filters],
    queryFn: () =>
      api
        .get("/activity", {
          params: {
            limit: filters.limit ?? 50,
            offset: filters.offset ?? 0,
            entity_type: filters.entity_type,
          },
        })
        .then((r) => r.data),
  });
}
