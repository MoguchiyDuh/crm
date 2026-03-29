import { Loader2, Plus, Search, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";
import { ProjectCard } from "@/components/common/ProjectCard";
import { ProjectForm, type ProjectFormValues } from "@/components/common/ProjectForm";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "@/components/ui/toaster";
import { useCreateProject, useProjects, type ProjectFilters } from "@/hooks/useProjects";
import { usePriorities, useStatuses } from "@/hooks/useReference";

export function Dashboard() {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState<ProjectFilters>({});
  const [search, setSearch] = useState("");

  const { data: projects, isLoading } = useProjects({ ...filters, search: search || undefined });
  const { data: statuses } = useStatuses();
  const { data: priorities } = usePriorities();
  const createProject = useCreateProject();

  function handleCreate(data: ProjectFormValues) {
    createProject.mutate(data, {
      onSuccess: () => {
        setOpen(false);
        toast({ title: "Project created" });
      },
      onError: () => toast({ title: "Error", variant: "destructive" }),
    });
  }

  const activeFilters = Object.values(filters).filter(Boolean).length;

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Projects</h1>
          <p className="text-sm text-muted-foreground">
            {projects?.length ?? 0} project{projects?.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4" />
              New project
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>New project</DialogTitle>
            </DialogHeader>
            <ProjectForm
              onSubmit={handleCreate}
              isPending={createProject.isPending}
              submitLabel="Create project"
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            className="pl-8 h-8 w-56 text-xs"
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <Select
          value={filters.status_id ? String(filters.status_id) : "all"}
          onValueChange={(v) =>
            setFilters((f) => ({ ...f, status_id: v === "all" ? undefined : Number(v) }))
          }
        >
          <SelectTrigger className="h-8 w-36 text-xs">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {statuses?.map((s) => (
              <SelectItem key={s.id} value={String(s.id)}>
                {s.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.priority_id ? String(filters.priority_id) : "all"}
          onValueChange={(v) =>
            setFilters((f) => ({ ...f, priority_id: v === "all" ? undefined : Number(v) }))
          }
        >
          <SelectTrigger className="h-8 w-36 text-xs">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All priorities</SelectItem>
            {priorities?.map((p) => (
              <SelectItem key={p.id} value={String(p.id)}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {activeFilters > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={() => setFilters({})}
          >
            <X className="h-3.5 w-3.5" />
            Clear ({activeFilters})
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : !projects?.length ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <SlidersHorizontal className="h-8 w-8 mb-2" />
          <p className="text-sm">No projects found</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}
