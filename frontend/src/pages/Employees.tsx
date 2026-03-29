import { zodResolver } from "@hookform/resolvers/zod";
import { Link2, Link2Off, Loader2, Mail, MoreHorizontal, Plus, Send, Trash2, UserCog } from "lucide-react";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import {
  useCreateEmployee,
  useDeleteEmployee,
  useEmployees,
  useLinkUser,
  useUnlinkUser,
  useUpdateEmployee,
} from "@/hooks/useEmployees";
import { useMe } from "@/hooks/useAuth";
import { useUsers } from "@/hooks/useUsers";
import { getInitials } from "@/lib/utils";
import type { Employee } from "@/types";

const schema = z.object({
  full_name: z.string().min(1, "Required"),
  role: z.string().min(1, "Required"),
  email: z.string().email().optional().or(z.literal("")),
  telegram: z.string().optional(),
  notes: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

function EmployeeFormDialog({
  employee,
  onClose,
}: {
  employee?: Employee;
  onClose: () => void;
}) {
  const create = useCreateEmployee();
  const update = useUpdateEmployee(employee?.id ?? 0);
  const isPending = create.isPending || update.isPending;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: employee?.full_name ?? "",
      role: employee?.role ?? "",
      email: employee?.email ?? "",
      telegram: employee?.telegram ?? "",
      notes: employee?.notes ?? "",
    },
  });

  function onSubmit(data: FormValues) {
    const payload = { ...data, email: data.email || undefined };
    if (employee) {
      update.mutate(payload, {
        onSuccess: () => { toast({ title: "Employee updated" }); onClose(); },
        onError: () => toast({ title: "Error", variant: "destructive" }),
      });
    } else {
      create.mutate(payload, {
        onSuccess: () => { toast({ title: "Employee created" }); onClose(); },
        onError: () => toast({ title: "Error", variant: "destructive" }),
      });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Full name *</Label>
          <Input {...register("full_name")} />
          {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label>Role *</Label>
          <Input {...register("role")} />
          {errors.role && <p className="text-xs text-destructive">{errors.role.message}</p>}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input type="email" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label>Telegram</Label>
          <Input {...register("telegram")} placeholder="@handle" />
        </div>
      </div>
      <div className="space-y-1.5">
        <Label>Notes</Label>
        <Textarea rows={2} {...register("notes")} />
      </div>
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        {employee ? "Save changes" : "Add employee"}
      </Button>
    </form>
  );
}

function LinkUserDialog({
  employee,
  onClose,
}: {
  employee: Employee;
  onClose: () => void;
}) {
  const { data: users } = useUsers();
  const link = useLinkUser(employee.id);
  const [selectedUserId, setSelectedUserId] = useState<string>("");

  // Filter out users already linked to other employees (we don't have that info here,
  // but the backend will reject anyway)
  const availableUsers = users?.filter((u) => u.is_active) ?? [];

  function handleSubmit() {
    if (!selectedUserId) return;
    link.mutate(Number(selectedUserId), {
      onSuccess: () => { toast({ title: "User linked" }); onClose(); },
      onError: (e: any) =>
        toast({
          title: e?.response?.data?.detail ?? "Link failed",
          variant: "destructive",
        }),
    });
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label>Select user account</Label>
        <Select value={selectedUserId} onValueChange={setSelectedUserId}>
          <SelectTrigger>
            <SelectValue placeholder="Choose user..." />
          </SelectTrigger>
          <SelectContent>
            {availableUsers.map((u) => (
              <SelectItem key={u.id} value={String(u.id)}>
                {u.email} ({u.role})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button
        className="w-full"
        disabled={!selectedUserId || link.isPending}
        onClick={handleSubmit}
      >
        {link.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        Link account
      </Button>
    </div>
  );
}

function EmployeeCard({ employee }: { employee: Employee }) {
  const [editOpen, setEditOpen] = useState(false);
  const [linkOpen, setLinkOpen] = useState(false);
  const deleteEmployee = useDeleteEmployee();
  const unlink = useUnlinkUser(employee.id);
  const { data: me } = useMe();
  const isAdmin = me?.role === "admin";

  function handleDelete() {
    deleteEmployee.mutate(employee.id, {
      onSuccess: () => toast({ title: "Employee removed" }),
      onError: () => toast({ title: "Error", variant: "destructive" }),
    });
  }

  function handleUnlink() {
    unlink.mutate(undefined, {
      onSuccess: () => toast({ title: "User unlinked" }),
      onError: () => toast({ title: "Unlink failed", variant: "destructive" }),
    });
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 flex items-start gap-3">
      <div className="h-9 w-9 rounded-full bg-accent flex items-center justify-center text-xs font-semibold shrink-0">
        {getInitials(employee.full_name)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-medium text-sm truncate">{employee.full_name}</p>
          {employee.user_id && (
            <span
              className="inline-flex items-center gap-1 text-xs text-primary"
              title={`Linked to user #${employee.user_id}`}
            >
              <Link2 className="h-3 w-3" />
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{employee.role}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          {employee.email && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Mail className="h-3 w-3" />
              {employee.email}
            </span>
          )}
          {employee.telegram && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Send className="h-3 w-3" />
              {employee.telegram}
            </span>
          )}
        </div>
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => setEditOpen(true)}>
            <UserCog className="h-4 w-4 mr-2" />
            Edit
          </DropdownMenuItem>
          {isAdmin && (
            <>
              <DropdownMenuSeparator />
              {employee.user_id ? (
                <DropdownMenuItem onClick={handleUnlink}>
                  <Link2Off className="h-4 w-4 mr-2" />
                  Unlink user
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => setLinkOpen(true)}>
                  <Link2 className="h-4 w-4 mr-2" />
                  Link user
                </DropdownMenuItem>
              )}
            </>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Remove
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit employee</DialogTitle>
          </DialogHeader>
          <EmployeeFormDialog employee={employee} onClose={() => setEditOpen(false)} />
        </DialogContent>
      </Dialog>

      <Dialog open={linkOpen} onOpenChange={setLinkOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Link user account</DialogTitle>
          </DialogHeader>
          <LinkUserDialog employee={employee} onClose={() => setLinkOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function Employees() {
  const [open, setOpen] = useState(false);
  const { data: employees, isLoading } = useEmployees();

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Team</h1>
          <p className="text-sm text-muted-foreground">
            {employees?.length ?? 0} member{employees?.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4" />
              Add member
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add team member</DialogTitle>
            </DialogHeader>
            <EmployeeFormDialog onClose={() => setOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {employees?.map((emp) => (
            <EmployeeCard key={emp.id} employee={emp} />
          ))}
        </div>
      )}
    </div>
  );
}
