import { Activity, BarChart3, FolderKanban, LogOut, Search, Shield, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { SearchModal } from "@/components/common/SearchModal";
import { SettingsModal } from "@/components/common/SettingsModal";
import { useLogout, useMe } from "@/hooks/useAuth";
import { useWebSocket } from "@/hooks/useWebSocket";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/employees", label: "Team", icon: Users },
  { to: "/activity", label: "Activity", icon: Activity },
];

export function Layout() {
  const logout = useLogout();
  const { data: me } = useMe();
  const { connected } = useWebSocket();
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen((o) => !o);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="flex h-screen bg-background">
      <aside className="flex w-56 flex-col border-r border-border bg-card">
        <div className="flex h-14 items-center px-4 border-b border-border">
          <BarChart3 className="h-5 w-5 mr-2 text-primary" />
          <span className="font-semibold text-sm flex-1">CRM</span>
          <span
            title={connected ? "Live" : "Reconnecting..."}
            className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-muted-foreground"}`}
          />
        </div>
        <button
          onClick={() => setSearchOpen(true)}
          className="flex items-center gap-2 mx-2 mt-3 px-3 py-2 rounded-md text-xs text-muted-foreground border border-border hover:bg-accent/50 transition-colors w-[calc(100%-1rem)]"
        >
          <Search className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1 text-left">Search...</span>
          <kbd className="border border-border rounded px-1 py-0.5 text-[10px]">⌘K</kbd>
        </button>

        <nav className="flex-1 space-y-1 p-2 pt-2">
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

      <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
