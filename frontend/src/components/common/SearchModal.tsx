import { FolderKanban, Loader2, Search, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSearch } from "@/hooks/useSearch";
import { cn } from "@/lib/utils";

function useDebounce(value: string, delay: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

interface SearchModalProps {
  open: boolean;
  onClose: () => void;
}

export function SearchModal({ open, onClose }: SearchModalProps) {
  const [query, setQuery] = useState("");
  const debouncedQ = useDebounce(query, 300);
  const { data, isFetching } = useSearch(debouncedQ);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [cursor, setCursor] = useState(0);

  const results = [
    ...(data?.projects.map((p) => ({ type: "project" as const, id: p.id, label: p.name, sub: p.client_name ?? undefined })) ?? []),
    ...(data?.employees.map((e) => ({ type: "employee" as const, id: e.id, label: e.full_name, sub: e.role })) ?? []),
  ];

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
      setCursor(0);
    }
  }, [open]);

  useEffect(() => setCursor(0), [debouncedQ]);

  function handleSelect(item: typeof results[number]) {
    if (item.type === "project") navigate(`/projects/${item.id}`);
    onClose();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter" && results[cursor]) {
      handleSelect(results[cursor]);
    } else if (e.key === "Escape") {
      onClose();
    }
  }

  if (!open) return null;

  const hasProjects = (data?.projects.length ?? 0) > 0;
  const hasEmployees = (data?.employees.length ?? 0) > 0;
  const projectOffset = 0;
  const employeeOffset = data?.projects.length ?? 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          {isFetching ? (
            <Loader2 className="h-4 w-4 text-muted-foreground animate-spin shrink-0" />
          ) : (
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search projects and team..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="text-xs text-muted-foreground border border-border rounded px-1.5 py-0.5">
            Esc
          </kbd>
        </div>

        {debouncedQ.length >= 2 && (
          <div className="max-h-80 overflow-y-auto py-2">
            {!hasProjects && !hasEmployees && !isFetching && (
              <p className="px-4 py-3 text-sm text-muted-foreground">No results for "{debouncedQ}"</p>
            )}

            {hasProjects && (
              <div>
                <p className="px-4 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Projects
                </p>
                {data!.projects.map((p, i) => (
                  <button
                    key={p.id}
                    onClick={() => handleSelect({ type: "project", id: p.id, label: p.name })}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors",
                      cursor === projectOffset + i
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent/50"
                    )}
                    onMouseEnter={() => setCursor(projectOffset + i)}
                  >
                    <FolderKanban className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="flex-1 truncate">{p.name}</span>
                    {p.client_name && (
                      <span className="text-xs text-muted-foreground shrink-0">{p.client_name}</span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {hasEmployees && (
              <div>
                <p className="px-4 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Team
                </p>
                {data!.employees.map((e, i) => (
                  <button
                    key={e.id}
                    onClick={() => handleSelect({ type: "employee", id: e.id, label: e.full_name })}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors",
                      cursor === employeeOffset + i
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent/50"
                    )}
                    onMouseEnter={() => setCursor(employeeOffset + i)}
                  >
                    <Users className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="flex-1 truncate">{e.full_name}</span>
                    <span className="text-xs text-muted-foreground shrink-0">{e.role}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {debouncedQ.length < 2 && (
          <div className="px-4 py-3 text-xs text-muted-foreground">
            Type at least 2 characters to search
          </div>
        )}
      </div>
    </div>
  );
}
