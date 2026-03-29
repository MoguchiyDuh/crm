import { createBrowserRouter, Navigate } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { RequireAuth } from "@/components/layout/RequireAuth";
import { Activity } from "@/pages/Activity";
import { Dashboard } from "@/pages/Dashboard";
import { Employees } from "@/pages/Employees";
import { Login } from "@/pages/Login";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { Users } from "@/pages/Users";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />,
  },
  {
    element: (
      <RequireAuth>
        <Layout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/projects" replace /> },
      { path: "projects", element: <Dashboard /> },
      { path: "projects/:id", element: <ProjectDetail /> },
      { path: "employees", element: <Employees /> },
      { path: "users", element: <Users /> },
      { path: "activity", element: <Activity /> },
    ],
  },
]);
