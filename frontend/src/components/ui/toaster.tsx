import * as ToastPrimitive from "@radix-ui/react-toast";
import { X } from "lucide-react";
import * as React from "react";
import { cn } from "@/lib/utils";

const ToastProvider = ToastPrimitive.Provider;
const ToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Viewport
    ref={ref}
    className={cn(
      "fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]",
      className
    )}
    {...props}
  />
));
ToastViewport.displayName = ToastPrimitive.Viewport.displayName;

interface ToastProps {
  id: string;
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
}

const toastState: { toasts: ToastProps[]; listeners: Array<() => void> } = {
  toasts: [],
  listeners: [],
};

export function toast(props: Omit<ToastProps, "id">) {
  const id = Math.random().toString(36).slice(2);
  toastState.toasts = [...toastState.toasts, { ...props, id }];
  toastState.listeners.forEach((l) => l());
  setTimeout(() => {
    toastState.toasts = toastState.toasts.filter((t) => t.id !== id);
    toastState.listeners.forEach((l) => l());
  }, 4000);
}

export function Toaster() {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  React.useEffect(() => {
    const listener = () => setToasts([...toastState.toasts]);
    toastState.listeners.push(listener);
    return () => {
      toastState.listeners = toastState.listeners.filter((l) => l !== listener);
    };
  }, []);

  return (
    <ToastProvider>
      {toasts.map(({ id, title, description, variant }) => (
        <ToastPrimitive.Root
          key={id}
          className={cn(
            "group pointer-events-auto relative flex w-full items-center justify-between space-x-2 overflow-hidden rounded-md border p-4 pr-6 shadow-lg transition-all",
            variant === "destructive"
              ? "border-destructive bg-destructive text-destructive-foreground"
              : "border bg-card text-card-foreground"
          )}
        >
          <div className="grid gap-1">
            {title && <ToastPrimitive.Title className="text-sm font-semibold">{title}</ToastPrimitive.Title>}
            {description && (
              <ToastPrimitive.Description className="text-sm opacity-90">
                {description}
              </ToastPrimitive.Description>
            )}
          </div>
          <ToastPrimitive.Close className="absolute right-1 top-1 rounded-md p-1 opacity-0 transition-opacity group-hover:opacity-100">
            <X className="h-4 w-4" />
          </ToastPrimitive.Close>
        </ToastPrimitive.Root>
      ))}
      <ToastViewport />
    </ToastProvider>
  );
}
