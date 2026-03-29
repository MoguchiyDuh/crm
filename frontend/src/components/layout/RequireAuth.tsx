import { Navigate } from "react-router-dom";

interface Props {
  children: React.ReactNode;
}

export function RequireAuth({ children }: Props) {
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
