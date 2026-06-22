import { CheckCircle2, Info, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";

type ToastTone = "success" | "info" | "error";

const iconByTone = {
  success: CheckCircle2,
  info: Info,
  error: TriangleAlert,
};

const toneClass: Record<ToastTone, string> = {
  success: "border-yes/30 bg-yes/10 text-foreground",
  info: "border-accent/30 bg-accent/10 text-foreground",
  error: "border-destructive/30 bg-destructive/10 text-foreground",
};

export function ToastPreview({
  title,
  description,
  tone = "info",
  className,
}: {
  title: string;
  description: string;
  tone?: ToastTone;
  className?: string;
}) {
  const Icon = iconByTone[tone];

  return (
    <div className={cn("flex max-w-sm gap-3 rounded-lg border p-3 shadow-surface", toneClass[tone], className)}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div className="min-w-0">
        <div className="text-sm font-semibold">{title}</div>
        <div className="mt-1 text-sm text-muted-foreground">{description}</div>
      </div>
    </div>
  );
}
