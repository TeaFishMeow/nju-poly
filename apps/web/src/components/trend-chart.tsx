"use client";

import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";

export function TrendChart({ values, className }: { values: number[]; className?: string }) {
  const t = useTranslations("design.trend");
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(1, values.length - 1)) * 100;
      const y = 100 - value;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className={cn("rounded-lg border bg-card p-4", className)}>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-semibold">{t("title")}</div>
        <div className="font-mono text-sm font-semibold text-primary">{values.at(-1)}%</div>
      </div>
      <svg viewBox="0 0 100 100" className="h-44 w-full overflow-visible" preserveAspectRatio="none" aria-hidden="true">
        {[25, 50, 75].map((y) => (
          <line key={y} x1="0" x2="100" y1={y} y2={y} stroke="hsl(var(--border))" strokeWidth="0.8" />
        ))}
        <polyline points={points} fill="none" stroke="hsl(var(--primary))" strokeWidth="3" vectorEffect="non-scaling-stroke" />
        <polyline
          points={`0,100 ${points} 100,100`}
          fill="hsl(var(--primary) / 0.12)"
          stroke="none"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="mt-2 flex justify-between font-mono text-xs text-muted-foreground">
        <span>{t("before")}</span>
        <span>{t("now")}</span>
      </div>
    </div>
  );
}
