import { Activity, BarChart3, FolderKanban, LogOut, Shield, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { SettingsModal } from "@/components/common/SettingsModal";
import { useLogout, useMe } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/employees", label: "Team", icon: Users },
  { to: "/activity", label: "Activity", icon: Activity },
];

export function Layout() {
  const logout = useLogout();
  const { data: me } = useMe();

  return (
    <div className="flex h-screen bg-background">
      <aside className="flex w-56 flex-col border-r border-border bg-card">
        <div className="flex h-14 items-center px-4 border-b border-border">
          <BarChart3 className="h-5 w-5 mr-2 text-primary" />
          <span className="font-semibold text-sm">CRM</span>
        </div>
        <nav className="flex-1 space-y-1 p-2 pt-4">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}

          {me?.role === "admin" && (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                )
              }
            >
              <Shield className="h-4 w-4" />
              Users
            </NavLink>
          )}
        </nav>
        <div className="p-2 border-t border-border space-y-1">
          <SettingsModal />
          <button
            onClick={() => logout.mutate()}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
