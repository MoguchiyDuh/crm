import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Settings } from "lucide-react";
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
import { toast } from "@/components/ui/toaster";
import { useMe } from "@/hooks/useAuth";
import { useUpdateMe } from "@/hooks/useUsers";

const schema = z
  .object({
    email: z.string().min(1, "Required"),
    current_password: z.string().optional(),
    new_password: z.string().optional(),
    confirm_password: z.string().optional(),
  })
  .refine(
    (d) => !d.new_password || d.new_password === d.confirm_password,
    { message: "Passwords don't match", path: ["confirm_password"] }
  )
  .refine(
    (d) => !d.new_password || !!d.current_password,
    { message: "Required to change password", path: ["current_password"] }
  );

type FormValues = z.infer<typeof schema>;

export function SettingsModal() {
  const [open, setOpen] = useState(false);
  const { data: me } = useMe();
  const updateMe = useUpdateMe();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: { email: me?.email ?? "" },
  });

  function onSubmit(data: FormValues) {
    updateMe.mutate(
      {
        email: data.email !== me?.email ? data.email : undefined,
        current_password: data.current_password || undefined,
        new_password: data.new_password || undefined,
      },
      {
        onSuccess: () => {
          toast({ title: "Settings saved" });
          reset({ email: data.email, current_password: "", new_password: "", confirm_password: "" });
          setOpen(false);
        },
        onError: (e: any) =>
          toast({ title: e?.response?.data?.detail ?? "Error", variant: "destructive" }),
      }
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors">
          <Settings className="h-4 w-4" />
          Settings
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Account settings</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input type="email" {...register("email")} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>

          <div className="border-t border-border pt-4 space-y-3">
            <p className="text-xs text-muted-foreground">Change password — leave blank to keep current</p>
            <div className="space-y-1.5">
              <Label>Current password</Label>
              <Input type="password" {...register("current_password")} />
              {errors.current_password && (
                <p className="text-xs text-destructive">{errors.current_password.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label>New password</Label>
              <Input type="password" {...register("new_password")} />
            </div>
            <div className="space-y-1.5">
              <Label>Confirm new password</Label>
              <Input type="password" {...register("confirm_password")} />
              {errors.confirm_password && (
                <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
              )}
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={updateMe.isPending}>
            {updateMe.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Save changes
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
