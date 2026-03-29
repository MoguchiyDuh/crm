import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import type { TokenResponse, User } from "@/types";

export function useMe() {
  return useQuery<User>({
    queryKey: ["me"],
    queryFn: () => api.get("/auth/me").then((r) => r.data),
    enabled: !!localStorage.getItem("access_token"),
    retry: false,
  });
}

export function useLogin() {
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (creds: { email: string; password: string }) =>
      api.post<TokenResponse>("/auth/login", creds).then((r) => r.data),
    onSuccess: (data) => {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      navigate("/projects");
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: () => api.post("/auth/logout"),
    onSettled: () => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      qc.clear();
      navigate("/login");
    },
  });
}
