import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Project } from "@/types";

export interface ProjectFilters {
  status_id?: number;
  priority_id?: number;
  manager_id?: number;
  search?: string;
}

const keys = {
  all: ["projects"] as const,
  list: (filters: ProjectFilters) => ["projects", filters] as const,
  detail: (id: number) => ["projects", id] as const,
};

export function useProjects(filters: ProjectFilters = {}) {
  return useQuery<Project[]>({
    queryKey: keys.list(filters),
    queryFn: () => api.get("/projects", { params: filters }).then((r) => r.data),
  });
}

export function useProject(id: number) {
  return useQuery<Project>({
    queryKey: keys.detail(id),
    queryFn: () => api.get(`/projects/${id}`).then((r) => r.data),
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Project>) => api.post<Project>("/projects", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useUpdateProject(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Project>) =>
      api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.all });
      qc.invalidateQueries({ queryKey: keys.detail(id) });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/projects/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}
