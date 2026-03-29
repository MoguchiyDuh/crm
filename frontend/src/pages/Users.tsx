import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Plus, Shield, Trash2, User as UserIcon } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
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
import { toast } from "@/components/ui/toaster";
import { useMe } from "@/hooks/useAuth";
import { useCreateUser, useDeleteUser, useUsers } from "@/hooks/useUsers";

const schema = z.object({
  email: z.string().min(1, "Required"),
  password: z.string().min(6, "Min 6 characters"),
  role: z.enum(["member", "admin"]),
});
type FormValues = z.infer<typeof schema>;

function CreateUserDialog({ onClose }: { onClose: () => void }) {
  const create = useCreateUser();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { role: "member" } });

  function onSubmit(data: FormValues) {
    create.mutate(data, {
      onSuccess: () => { toast({ title: "User created" }); onClose(); },
      onError: (e: any) =>
        toast({ title: e?.response?.data?.detail ?? "Error", variant: "destructive" }),
    });
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label>Email</Label>
        <Input type="email" {...register("email")} />
        {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
      </div>
      <div className="space-y-1.5">
        <Label>Password</Label>
        <Input type="password" {...register("password")} />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
      </div>
      <div className="space-y-1.5">
        <Label>Role</Label>
        <Select value={watch("role")} onValueChange={(v) => setValue("role", v as "member" | "admin")}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="member">Member</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button type="submit" className="w-full" disabled={create.isPending}>
        {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        Create user
      </Button>
    </form>
  );
}

export function Users() {
  const [open, setOpen] = useState(false);
  const { data: users, isLoading } = useUsers();
  const { data: me } = useMe();
  const deleteUser = useDeleteUser();

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Users</h1>
          <p className="text-sm text-muted-foreground">{users?.length ?? 0} accounts</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm"><Plus className="h-4 w-4" />New user</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create user</DialogTitle></DialogHeader>
            <CreateUserDialog onClose={() => setOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Email</th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Role</th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Status</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody>
              {users?.map((user) => (
                <tr key={user.id} className="border-b border-border last:border-0 hover:bg-accent/20">
                  <td className="px-4 py-3 flex items-center gap-2">
                    {user.role === "admin"
                      ? <Shield className="h-3.5 w-3.5 text-primary shrink-0" />
                      : <UserIcon className="h-3.5 w-3.5 text-muted-foreground shrink-0" />}
                    {user.email}
                    {user.id === me?.id && (
                      <span className="text-xs text-muted-foreground">(you)</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                      {user.role}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs ${user.is_active ? "text-green-400" : "text-muted-foreground"}`}>
                      {user.is_active ? "active" : "inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {user.id !== me?.id && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        onClick={() =>
                          deleteUser.mutate(user.id, {
                            onSuccess: () => toast({ title: "User deleted" }),
                            onError: () => toast({ title: "Error", variant: "destructive" }),
                          })
                        }
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
