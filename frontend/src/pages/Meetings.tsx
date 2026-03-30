import { zodResolver } from "@hookform/resolvers/zod";
import {
  Calendar,
  ExternalLink,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  UserMinus,
  UserPlus,
  Users,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toaster";
import { useEmployees } from "@/hooks/useEmployees";
import {
  useAddParticipant,
  useCreateMeeting,
  useDeleteMeeting,
  useMeetings,
  useRemoveParticipant,
  useUpdateMeeting,
} from "@/hooks/useMeetings";
import { useProjects } from "@/hooks/useProjects";
import { cn, formatDate, getInitials } from "@/lib/utils";
import type { Meeting } from "@/types";

const STATUSES = ["scheduled", "in_progress", "done", "cancelled"] as const;

const createSchema = z.object({
  title: z.string().min(1, "Required"),
  scheduled_at: z.string().min(1, "Required"),
  project_id: z.coerce.number().min(1, "Required"),
  meeting_link: z.string().url().optional().or(z.literal("")),
  notes: z.string().optional(),
});
type CreateValues = z.infer<typeof createSchema>;

const editSchema = z.object({
  title: z.string().min(1, "Required"),
  scheduled_at: z.string().min(1, "Required"),
  status: z.string().min(1),
  meeting_link: z.string().url().optional().or(z.literal("")),
  notes: z.string().optional(),
});
type EditValues = z.infer<typeof editSchema>;

function toDatetimeLocal(iso: string) {
  return iso.slice(0, 16);
}

function statusBadgeClass(status: string) {
  return {
    scheduled: "bg-blue-500/10 text-blue-600 border-blue-500/20",
    in_progress: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
    done: "bg-green-500/10 text-green-600 border-green-500/20",
    cancelled: "bg-muted text-muted-foreground",
  }[status] ?? "bg-muted text-muted-foreground";
}

// ── Create dialog ──────────────────────────────────────────────────────────

function CreateMeetingDialog() {
  const [open, setOpen] = useState(false);
  const [participants, setParticipants] = useState<number[]>([]);
  const { data: projects } = useProjects();
  const { data: employees } = useEmployees();
  const create = useCreateMeeting();

  const { register, handleSubmit, setValue, formState: { errors }, reset } =
    useForm<CreateValues>({ resolver: zodResolver(createSchema) });

  function toggle(id: number) {
    setParticipants((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id]);
  }

  function onSubmit(data: CreateValues) {
    create.mutate(
      { ...data, meeting_link: data.meeting_link || undefined, participant_ids: participants },
      {
        onSuccess: () => {
          toast({ title: "Meeting scheduled" });
          reset();
          setParticipants([]);
          setOpen(false);
        },
        onError: () => toast({ title: "Error", variant: "destructive" }),
      }
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-3.5 w-3.5" />
          New meeting
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Schedule meeting</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Title *</Label>
            <Input {...register("title")} />
            {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Project *</Label>
            <Select onValueChange={(v) => setValue("project_id", Number(v))}>
              <SelectTrigger>
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {projects?.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.project_id && <p className="text-xs text-destructive">{errors.project_id.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Date & time *</Label>
            <Input type="datetime-local" {...register("scheduled_at")} />
            {errors.scheduled_at && <p className="text-xs text-destructive">{errors.scheduled_at.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Meeting link</Label>
            <Input type="url" {...register("meeting_link")} placeholder="https://..." />
          </div>
          <div className="space-y-1.5">
            <Label>Notes</Label>
            <Textarea rows={2} {...register("notes")} />
          </div>
          <div className="space-y-1.5">
            <Label>Participants</Label>
            <div className="grid grid-cols-2 gap-1.5 max-h-32 overflow-y-auto">
              {employees?.map((emp) => (
                <button
                  key={emp.id}
                  type="button"
                  onClick={() => toggle(emp.id)}
                  className={cn(
                    "text-left px-2 py-1.5 rounded text-xs border transition-colors",
                    participants.includes(emp.id)
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border hover:bg-accent"
                  )}
                >
                  {emp.full_name}
                </button>
              ))}
            </div>
          </div>
          <Button type="submit" className="w-full" disabled={create.isPending}>
            {create.isPending && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
            Schedule
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Edit dialog ────────────────────────────────────────────────────────────

function EditMeetingDialog({ meeting }: { meeting: Meeting }) {
  const [open, setOpen] = useState(false);
  const update = useUpdateMeeting(meeting.id);

  const { register, handleSubmit, setValue, formState: { errors } } =
    useForm<EditValues>({
      resolver: zodResolver(editSchema),
      defaultValues: {
        title: meeting.title,
        scheduled_at: toDatetimeLocal(meeting.scheduled_at),
        status: meeting.status,
        meeting_link: meeting.meeting_link ?? "",
        notes: meeting.notes ?? "",
      },
    });

  function onSubmit(data: EditValues) {
    update.mutate(
      { ...data, meeting_link: data.meeting_link || null, notes: data.notes || null },
      {
        onSuccess: () => { toast({ title: "Meeting updated" }); setOpen(false); },
        onError: () => toast({ title: "Error", variant: "destructive" }),
      }
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground">
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit meeting</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Title *</Label>
            <Input {...register("title")} />
            {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Date & time *</Label>
            <Input type="datetime-local" {...register("scheduled_at")} />
          </div>
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select defaultValue={meeting.status} onValueChange={(v) => setValue("status", v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>{s.replace("_", " ")}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Meeting link</Label>
            <Input type="url" {...register("meeting_link")} placeholder="https://..." />
          </div>
          <div className="space-y-1.5">
            <Label>Notes</Label>
            <Textarea rows={3} {...register("notes")} />
          </div>
          <Button type="submit" className="w-full" disabled={update.isPending}>
            {update.isPending && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
            Save changes
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Participants popover ───────────────────────────────────────────────────

function ParticipantsDialog({ meeting }: { meeting: Meeting }) {
  const [open, setOpen] = useState(false);
  const { data: employees } = useEmployees();
  const addParticipant = useAddParticipant(meeting.id);
  const removeParticipant = useRemoveParticipant(meeting.id);

  const currentIds = new Set(meeting.participants.map((p) => p.employee.id));

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
          <Users className="h-3 w-3" />
          {meeting.participants.length}
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Participants — {meeting.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-1 max-h-72 overflow-y-auto">
          {employees?.map((emp) => {
            const isIn = currentIds.has(emp.id);
            return (
              <div key={emp.id} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-accent text-sm">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-accent text-xs font-medium">
                    {getInitials(emp.full_name)}
                  </span>
                  <span>{emp.full_name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() =>
                    isIn
                      ? removeParticipant.mutate(emp.id)
                      : addParticipant.mutate(emp.id)
                  }
                >
                  {isIn
                    ? <UserMinus className="h-3.5 w-3.5 text-destructive" />
                    : <UserPlus className="h-3.5 w-3.5 text-muted-foreground" />
                  }
                </Button>
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Meeting row ────────────────────────────────────────────────────────────

function MeetingRow({ meeting, projectName }: { meeting: Meeting; projectName: string }) {
  const deleteMeeting = useDeleteMeeting();

  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4">
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium">{meeting.title}</p>
          <Badge className={cn("text-xs border", statusBadgeClass(meeting.status))}>
            {meeting.status.replace("_", " ")}
          </Badge>
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDate(meeting.scheduled_at)}
          </span>
          <Link
            to={`/projects/${meeting.project_id}`}
            className="hover:text-foreground transition-colors"
          >
            {projectName}
          </Link>
          <ParticipantsDialog meeting={meeting} />
          {meeting.meeting_link && (
            <a
              href={meeting.meeting_link}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:text-foreground"
            >
              <ExternalLink className="h-3 w-3" />
              Link
            </a>
          )}
        </div>
        {meeting.participants.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {meeting.participants.map((p) => (
              <span
                key={p.id}
                title={p.employee.full_name}
                className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-accent text-xs font-medium"
              >
                {getInitials(p.employee.full_name)}
              </span>
            ))}
          </div>
        )}
        {meeting.notes && (
          <p className="text-xs text-muted-foreground">{meeting.notes}</p>
        )}
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <EditMeetingDialog meeting={meeting} />
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-destructive"
          onClick={() =>
            deleteMeeting.mutate(meeting.id, {
              onSuccess: () => toast({ title: "Meeting deleted" }),
              onError: () => toast({ title: "Error", variant: "destructive" }),
            })
          }
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export function Meetings() {
  const { data: meetings, isLoading } = useMeetings();
  const { data: projects } = useProjects();
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const projectMap = Object.fromEntries(projects?.map((p) => [p.id, p.name]) ?? []);

  const filtered = meetings?.filter(
    (m) => statusFilter === "all" || m.status === statusFilter
  ) ?? [];

  return (
    <div className="p-6 space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Meetings</h1>
          <p className="text-sm text-muted-foreground">{meetings?.length ?? 0} total</p>
        </div>
        <CreateMeetingDialog />
      </div>

      {/* Status filter */}
      <div className="flex gap-2 flex-wrap">
        {["all", ...STATUSES].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
              statusFilter === s
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:bg-accent"
            )}
          >
            {s === "all" ? "All" : s.replace("_", " ")}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}

      {!isLoading && filtered.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">No meetings.</p>
      )}

      <div className="space-y-2">
        {filtered.map((meeting) => (
          <MeetingRow
            key={meeting.id}
            meeting={meeting}
            projectName={projectMap[meeting.project_id] ?? `Project #${meeting.project_id}`}
          />
        ))}
      </div>
    </div>
  );
}
