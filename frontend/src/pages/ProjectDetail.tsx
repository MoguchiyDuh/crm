import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Calendar,
  ExternalLink,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  Users,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import { AttachmentList } from "@/components/common/AttachmentList";
import { ProjectForm, type ProjectFormValues } from "@/components/common/ProjectForm";
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
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toaster";
import { useEmployees } from "@/hooks/useEmployees";
import { useCreateMeeting, useDeleteMeeting, useMeetings } from "@/hooks/useMeetings";
import { useDeleteProject, useProject, useUpdateProject } from "@/hooks/useProjects";
import { formatDate, getInitials } from "@/lib/utils";

const meetingSchema = z.object({
  title: z.string().min(1, "Required"),
  scheduled_at: z.string().min(1, "Required"),
  meeting_link: z.string().url().optional().or(z.literal("")),
  notes: z.string().optional(),
  participant_ids: z.array(z.number()).default([]),
});
type MeetingFormValues = z.infer<typeof meetingSchema>;

function MeetingForm({
  projectId,
  onClose,
}: {
  projectId: number;
  onClose: () => void;
}) {
  const createMeeting = useCreateMeeting();
  const { data: employees } = useEmployees();
  const [selectedParticipants, setSelectedParticipants] = useState<number[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<MeetingFormValues>({
    resolver: zodResolver(meetingSchema),
    defaultValues: { participant_ids: [] },
  });

  function toggleParticipant(id: number) {
    setSelectedParticipants((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function onSubmit(data: MeetingFormValues) {
    createMeeting.mutate(
      {
        ...data,
        project_id: projectId,
        meeting_link: data.meeting_link || undefined,
        participant_ids: selectedParticipants,
      },
      {
        onSuccess: () => { toast({ title: "Meeting scheduled" }); onClose(); },
        onError: () => toast({ title: "Error", variant: "destructive" }),
      }
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label>Title *</Label>
        <Input {...register("title")} />
        {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
      </div>
      <div className="space-y-1.5">
        <Label>Date & time *</Label>
        <Input type="datetime-local" {...register("scheduled_at")} />
        {errors.scheduled_at && (
          <p className="text-xs text-destructive">{errors.scheduled_at.message}</p>
        )}
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
              onClick={() => toggleParticipant(emp.id)}
              className={`text-left px-2 py-1.5 rounded text-xs border transition-colors ${
                selectedParticipants.includes(emp.id)
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border hover:bg-accent"
              }`}
            >
              {emp.full_name}
            </button>
          ))}
        </div>
      </div>
      <Button type="submit" className="w-full" disabled={createMeeting.isPending}>
        {createMeeting.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        Schedule meeting
      </Button>
    </form>
  );
}

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const navigate = useNavigate();

  const { data: project, isLoading } = useProject(projectId);
  const { data: meetings } = useMeetings();
  const updateProject = useUpdateProject(projectId);
  const deleteProject = useDeleteProject();

  const [editOpen, setEditOpen] = useState(false);
  const [meetingOpen, setMeetingOpen] = useState(false);
  const deleteMeeting = useDeleteMeeting();

  const projectMeetings = meetings?.filter((m) => m.project_id === projectId) ?? [];

  function handleUpdate(data: ProjectFormValues) {
    updateProject.mutate(data, {
      onSuccess: () => { toast({ title: "Project updated" }); setEditOpen(false); },
      onError: () => toast({ title: "Error", variant: "destructive" }),
    });
  }

  function handleDelete() {
    if (!confirm("Delete this project?")) return;
    deleteProject.mutate(projectId, {
      onSuccess: () => { toast({ title: "Project deleted" }); navigate("/projects"); },
      onError: () => toast({ title: "Error", variant: "destructive" }),
    });
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <p>Project not found.</p>
        <Link to="/projects" className="text-sm underline mt-2 inline-block">
          Back to projects
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link
          to="/projects"
          className="mt-1 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold">{project.name}</h1>
          {project.description && (
            <p className="text-sm text-muted-foreground mt-0.5">{project.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Pencil className="h-3.5 w-3.5" />
                Edit
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Edit project</DialogTitle>
              </DialogHeader>
              <ProjectForm
                defaultValues={project}
                onSubmit={handleUpdate}
                isPending={updateProject.isPending}
                submitLabel="Save changes"
              />
            </DialogContent>
          </Dialog>
          <Button variant="destructive" size="sm" onClick={handleDelete}>
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Meta cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground mb-1">Status</p>
          <Badge variant="secondary">{project.status.name}</Badge>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground mb-1">Priority</p>
          <p className="text-sm font-medium">{project.priority.name}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground mb-1">Manager</p>
          <p className="text-sm font-medium">{project.manager?.full_name ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground mb-1">Client</p>
          <p className="text-sm font-medium">{project.client_name ?? "—"}</p>
        </div>
      </div>

      {/* Progress */}
      <div className="rounded-lg border border-border bg-card p-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium">Progress</span>
          <span className="text-muted-foreground">{project.progress}%</span>
        </div>
        <Progress value={project.progress} />
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-3 rounded-lg border border-border bg-card p-4 text-sm">
        <div>
          <p className="text-xs text-muted-foreground">Start date</p>
          <p>{formatDate(project.start_date)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Deadline</p>
          <p>{formatDate(project.deadline_date)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Budget</p>
          <p>{project.budget != null ? `$${project.budget.toLocaleString()}` : "—"}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Spent hours</p>
          <p>{project.spent_hours ?? "—"}</p>
        </div>
        {project.client_contact && (
          <div className="col-span-2">
            <p className="text-xs text-muted-foreground">Client contact</p>
            <p>{project.client_contact}</p>
          </div>
        )}
        {project.tags && (
          <div className="col-span-2">
            <p className="text-xs text-muted-foreground mb-1.5">Tags</p>
            <div className="flex flex-wrap gap-1.5">
              {project.tags.split(",").map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag.trim()}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Attachments */}
      <AttachmentList projectId={projectId} />

      {/* Meetings */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium text-sm">
            Meetings <span className="text-muted-foreground">({projectMeetings.length})</span>
          </h2>
          <Dialog open={meetingOpen} onOpenChange={setMeetingOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="h-3.5 w-3.5" />
                Schedule
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Schedule meeting</DialogTitle>
              </DialogHeader>
              <MeetingForm projectId={projectId} onClose={() => setMeetingOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>

        {projectMeetings.length === 0 ? (
          <p className="text-sm text-muted-foreground">No meetings yet.</p>
        ) : (
          <div className="space-y-2">
            {projectMeetings.map((meeting) => (
              <div
                key={meeting.id}
                className="flex items-center gap-3 rounded-lg border border-border bg-card p-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium truncate">{meeting.title}</p>
                    <Badge variant="outline" className="text-xs shrink-0">
                      {meeting.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(meeting.scheduled_at)}
                    </span>
                    {meeting.participants.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        {meeting.participants.length}
                      </span>
                    )}
                    {meeting.meeting_link && (
                      <a
                        href={meeting.meeting_link}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="h-3 w-3" />
                        Link
                      </a>
                    )}
                  </div>
                  {meeting.participants.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {meeting.participants.map((p) => (
                        <span
                          key={p.id}
                          className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-accent text-xs font-medium"
                          title={p.employee.full_name}
                        >
                          {getInitials(p.employee.full_name)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
                  onClick={() =>
                    deleteMeeting.mutate(meeting.id, {
                      onSuccess: () => toast({ title: "Meeting deleted" }),
                    })
                  }
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
