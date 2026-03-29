import { Calendar, User } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { formatDate } from "@/lib/utils";
import type { Project } from "@/types";

interface Props {
  project: Project;
}

const PRIORITY_COLORS: Record<string, string> = {
  Critical: "bg-red-500/20 text-red-400 border-red-500/30",
  High: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  Medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  Low: "bg-green-500/20 text-green-400 border-green-500/30",
};

export function ProjectCard({ project }: Props) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="block rounded-lg border border-border bg-card p-4 hover:bg-accent/30 transition-colors"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <h3 className="font-medium text-sm leading-tight line-clamp-2">{project.name}</h3>
        <span
          className={`shrink-0 inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold ${
            PRIORITY_COLORS[project.priority.name] ?? "bg-secondary text-secondary-foreground"
          }`}
        >
          {project.priority.name}
        </span>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <Badge variant="secondary" className="text-xs">
          {project.status.name}
        </Badge>
        {project.client_name && (
          <span className="text-xs text-muted-foreground truncate">{project.client_name}</span>
        )}
      </div>

      <div className="space-y-1.5 mb-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Progress</span>
          <span>{project.progress}%</span>
        </div>
        <Progress value={project.progress} className="h-1.5" />
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        {project.manager ? (
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {project.manager.full_name.split(" ")[0]}
          </span>
        ) : (
          <span />
        )}
        {project.deadline_date && (
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDate(project.deadline_date)}
          </span>
        )}
      </div>
    </Link>
  );
}
