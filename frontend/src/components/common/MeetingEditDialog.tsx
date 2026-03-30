import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Pencil } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
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
import { useUpdateMeeting } from "@/hooks/useMeetings";
import type { Meeting } from "@/types";

const STATUSES = ["scheduled", "in_progress", "done", "cancelled"] as const;

const schema = z.object({
  title: z.string().min(1, "Required"),
  scheduled_at: z.string().min(1, "Required"),
  status: z.string().min(1),
  meeting_link: z.string().url().optional().or(z.literal("")),
  notes: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export function MeetingEditDialog({ meeting }: { meeting: Meeting }) {
  const [open, setOpen] = useState(false);
  const update = useUpdateMeeting(meeting.id);

  const { register, handleSubmit, setValue, formState: { errors } } =
    useForm<FormValues>({
      resolver: zodResolver(schema),
      defaultValues: {
        title: meeting.title,
        scheduled_at: meeting.scheduled_at.slice(0, 16),
        status: meeting.status,
        meeting_link: meeting.meeting_link ?? "",
        notes: meeting.notes ?? "",
      },
    });

  function onSubmit(data: FormValues) {
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
