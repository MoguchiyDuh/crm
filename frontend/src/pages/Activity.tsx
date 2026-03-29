import { Activity as ActivityIcon, Loader2 } from "lucide-react";
import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useActivity } from "@/hooks/useActivity";
import type { ActivityLog } from "@/types";

const ACTION_COLORS: Record<string, string> = {
  created: "text-green-400",
  updated: "text-blue-400",
  deleted: "text-red-400",
  linked: "text-purple-400",
  unlinked: "text-orange-400",
};

function LogRow({ log }: { log: ActivityLog }) {
  const color = ACTION_COLORS[log.action] ?? "text-muted-foreground";
  const date = new Date(log.created_at).toLocaleString();

  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border last:border-0">
      <div className="shrink-0 mt-0.5">
        <ActivityIcon className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0 text-sm">
        <span className="text-muted-foreground">{log.user_email ?? "system"}</span>
        {" "}
        <span className={`font-medium ${color}`}>{log.action}</span>
        {" "}
        <span className="text-muted-foreground">{log.entity_type}</span>
        {log.entity_name && (
          <>
            {" "}<span className="font-medium truncate">{log.entity_name}</span>
          </>
        )}
      </div>
      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">{date}</span>
    </div>
  );
}

export function Activity() {
  const [entityType, setEntityType] = useState<string>("all");
  const { data: logs, isLoading } = useActivity({
    entity_type: entityType === "all" ? undefined : entityType,
    limit: 100,
  });

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Activity Log</h1>
          <p className="text-sm text-muted-foreground">{logs?.length ?? 0} entries</p>
        </div>
        <Select value={entityType} onValueChange={setEntityType}>
          <SelectTrigger className="h-8 w-40 text-xs">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="project">Projects</SelectItem>
            <SelectItem value="employee">Employees</SelectItem>
            <SelectItem value="meeting">Meetings</SelectItem>
            <SelectItem value="user">Users</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-lg border border-border bg-card px-4">
        {isLoading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : !logs?.length ? (
          <p className="py-10 text-center text-sm text-muted-foreground">No activity yet.</p>
        ) : (
          logs.map((log) => <LogRow key={log.id} log={log} />)
        )}
      </div>
    </div>
  );
}
