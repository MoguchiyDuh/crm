import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Meeting } from "@/types";

const keys = {
  all: ["meetings"] as const,
  detail: (id: number) => ["meetings", id] as const,
};

export function useMeetings() {
  return useQuery<Meeting[]>({
    queryKey: keys.all,
    queryFn: () => api.get("/meetings").then((r) => r.data),
  });
}

export function useCreateMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      title: string;
      scheduled_at: string;
      project_id: number;
      meeting_link?: string;
      notes?: string;
      participant_ids?: number[];
    }) => api.post<Meeting>("/meetings", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useDeleteMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/meetings/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useAddParticipant(meetingId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (employeeId: number) =>
      api.post(`/meetings/${meetingId}/participants/${employeeId}`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useRemoveParticipant(meetingId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (employeeId: number) =>
      api.delete(`/meetings/${meetingId}/participants/${employeeId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}
