import { cn } from "@/lib/utils";

export function ProbabilityBar({
  yes,
  className,
}: {
  yes: number;
  className?: string;
}) {
  const boundedYes = Math.max(0, Math.min(100, yes));
  const no = 100 - boundedYes;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between font-mono text-xs font-semibold text-muted-foreground">
        <span>YES {boundedYes}%</span>
        <span>NO {no}%</span>
      </div>
      <div className="flex h-2 overflow-hidden rounded-sm bg-muted">
        <div className="bg-yes" style={{ width: `${boundedYes}%` }} />
        <div className="bg-no" style={{ width: `${no}%` }} />
      </div>
    </div>
  );
}
