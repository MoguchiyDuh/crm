import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Employee } from "@/types";

const keys = {
  all: ["employees"] as const,
};

export function useEmployees() {
  return useQuery<Employee[]>({
    queryKey: keys.all,
    queryFn: () => api.get("/employees").then((r) => r.data),
  });
}

export function useCreateEmployee() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Employee>) =>
      api.post<Employee>("/employees", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useUpdateEmployee(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Employee>) =>
      api.patch<Employee>(`/employees/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useDeleteEmployee() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/employees/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useLinkUser(employeeId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: number) =>
      api.post<Employee>(`/employees/${employeeId}/link`, { user_id: userId }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useUnlinkUser(employeeId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.delete<Employee>(`/employees/${employeeId}/link`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}
