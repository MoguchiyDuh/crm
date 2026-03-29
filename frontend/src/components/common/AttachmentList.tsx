import { Download, FileIcon, Loader2, Paperclip, Trash2, Upload } from "lucide-react";
import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toaster";
import type { Attachment } from "@/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface AttachmentListProps {
  projectId: number;
}

export function AttachmentList({ projectId }: AttachmentListProps) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const queryKey = ["attachments", projectId];

  const { data: attachments, isLoading } = useQuery<Attachment[]>({
    queryKey,
    queryFn: () => api.get(`/projects/${projectId}/attachments`).then((r) => r.data),
  });

  const upload = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.post(`/projects/${projectId}/attachments`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey });
      toast({ title: "File uploaded" });
    },
    onError: () => toast({ title: "Upload failed", variant: "destructive" }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/attachments/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey });
      toast({ title: "File deleted" });
    },
    onError: () => toast({ title: "Delete failed", variant: "destructive" }),
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file);
    e.target.value = "";
  }

  function handleDownload(attachment: Attachment) {
    const token = localStorage.getItem("access_token");
    const link = document.createElement("a");
    link.href = `/api/attachments/${attachment.id}/download`;
    link.download = attachment.filename;
    // Add auth via fetch instead
    fetch(`/api/attachments/${attachment.id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
      });
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-sm">
          Attachments{" "}
          <span className="text-muted-foreground">({attachments?.length ?? 0})</span>
        </h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => fileRef.current?.click()}
          disabled={upload.isPending}
        >
          {upload.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Upload className="h-3.5 w-3.5" />
          )}
          Upload
        </Button>
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-4">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
      ) : !attachments?.length ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
          <Paperclip className="h-3.5 w-3.5" />
          No attachments
        </div>
      ) : (
        <div className="space-y-1.5">
          {attachments.map((a) => (
            <div
              key={a.id}
              className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2"
            >
              <FileIcon className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="flex-1 text-sm truncate">{a.filename}</span>
              <span className="text-xs text-muted-foreground shrink-0">{formatBytes(a.size)}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 shrink-0"
                onClick={() => handleDownload(a)}
              >
                <Download className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 shrink-0 text-muted-foreground hover:text-destructive"
                onClick={() => remove.mutate(a.id)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
