import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
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
import { useEmployees } from "@/hooks/useEmployees";
import { usePriorities, useStatuses } from "@/hooks/useReference";
import type { Project } from "@/types";

const schema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
  status_id: z.coerce.number().min(1, "Required"),
  priority_id: z.coerce.number().min(1, "Required"),
  manager_id: z.coerce.number().nullable().optional(),
  client_name: z.string().optional(),
  client_contact: z.string().optional(),
  start_date: z.string().optional(),
  deadline_date: z.string().optional(),
  budget: z.coerce.number().nullable().optional(),
  progress: z.coerce.number().min(0).max(100).default(0),
  tags: z.string().optional(),
});

export type ProjectFormValues = z.infer<typeof schema>;

interface Props {
  defaultValues?: Partial<Project>;
  onSubmit: (data: ProjectFormValues) => void;
  isPending: boolean;
  submitLabel: string;
}

export function ProjectForm({ defaultValues, onSubmit, isPending, submitLabel }: Props) {
  const { data: statuses } = useStatuses();
  const { data: priorities } = usePriorities();
  const { data: employees } = useEmployees();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: defaultValues?.name ?? "",
      description: defaultValues?.description ?? "",
      status_id: defaultValues?.status?.id ?? 0,
      priority_id: defaultValues?.priority?.id ?? 0,
      manager_id: defaultValues?.manager?.id ?? null,
      client_name: defaultValues?.client_name ?? "",
      client_contact: defaultValues?.client_contact ?? "",
      start_date: defaultValues?.start_date?.slice(0, 10) ?? "",
      deadline_date: defaultValues?.deadline_date?.slice(0, 10) ?? "",
      budget: defaultValues?.budget ?? undefined,
      progress: defaultValues?.progress ?? 0,
      tags: defaultValues?.tags ?? "",
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label>Name *</Label>
        <Input {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label>Description</Label>
        <Textarea rows={3} {...register("description")} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Status *</Label>
          <Select
            value={String(watch("status_id") || "")}
            onValueChange={(v) => setValue("status_id", Number(v))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              {statuses?.map((s) => (
                <SelectItem key={s.id} value={String(s.id)}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.status_id && <p className="text-xs text-destructive">{errors.status_id.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label>Priority *</Label>
          <Select
            value={String(watch("priority_id") || "")}
            onValueChange={(v) => setValue("priority_id", Number(v))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select priority" />
            </SelectTrigger>
            <SelectContent>
              {priorities?.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.priority_id && <p className="text-xs text-destructive">{errors.priority_id.message}</p>}
        </div>
      </div>

      <div className="space-y-1.5">
        <Label>Manager</Label>
        <Select
          value={watch("manager_id") ? String(watch("manager_id")) : "none"}
          onValueChange={(v) => setValue("manager_id", v === "none" ? null : Number(v))}
        >
          <SelectTrigger>
            <SelectValue placeholder="No manager" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No manager</SelectItem>
            {employees?.map((e) => (
              <SelectItem key={e.id} value={String(e.id)}>
                {e.full_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Client name</Label>
          <Input {...register("client_name")} />
        </div>
        <div className="space-y-1.5">
          <Label>Client contact</Label>
          <Input {...register("client_contact")} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Start date</Label>
          <Input type="date" {...register("start_date")} />
        </div>
        <div className="space-y-1.5">
          <Label>Deadline</Label>
          <Input type="date" {...register("deadline_date")} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Budget</Label>
          <Input type="number" {...register("budget")} />
        </div>
        <div className="space-y-1.5">
          <Label>Progress (%)</Label>
          <Input type="number" min={0} max={100} {...register("progress")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label>Tags (comma-separated)</Label>
        <Input {...register("tags")} placeholder="web, backend, api" />
      </div>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        {submitLabel}
      </Button>
    </form>
  );
}
