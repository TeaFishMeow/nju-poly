"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { generatedBrandLogoPath } from "@/generated/brand-art";
import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  const [imageFailed, setImageFailed] = useState(false);

  if (!imageFailed) {
    return (
      <img
        src={generatedBrandLogoPath}
        alt=""
        aria-hidden="true"
        className={cn("h-9 w-9 rounded-lg object-cover", className)}
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <svg className={cn("h-9 w-9", className)} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <rect width="40" height="40" rx="8" fill="currentColor" className="text-primary" />
      <path d="M10 27V14.5L20 9l10 5.5V27" stroke="white" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M13 25h14" stroke="white" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M14 19.5l4 2.5 4.5-6 3.5 3" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function BrandLockup({ className }: { className?: string }) {
  return (
    <div className={cn("flex min-w-0 items-center gap-3", className)}>
      <BrandMark className="shrink-0" />
      <div className="min-w-0">
        <div className="truncate font-display text-lg font-semibold leading-none">南哪竞猜</div>
        <div className="mt-1 text-xs font-semibold uppercase tracking-normal text-muted-foreground">NJUPoly</div>
      </div>
    </div>
  );
}

export function LogoCandidate({
  variant,
  selected = false,
}: {
  variant: "gate" | "ticket" | "bars";
  selected?: boolean;
}) {
  const t = useTranslations("design.logo");

  if (variant === "gate") {
    return (
      <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
        <BrandMark className="h-12 w-12" />
        <div>
          <div className="font-semibold">{t("gate")}</div>
          <div className="text-sm text-muted-foreground">{selected ? t("selected") : t("candidate")}</div>
        </div>
      </div>
    );
  }

  if (variant === "ticket") {
    return (
      <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
        <svg className="h-12 w-12 text-accent" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <path d="M9 13h30v22H9V13Z" fill="currentColor" />
          <path d="M15 30l6-9 5 5 7-10" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M9 20c3 0 3-5 0-5M39 20c-3 0-3-5 0-5M9 30c3 0 3 5 0 5M39 30c-3 0-3 5 0 5" stroke="hsl(var(--background))" strokeWidth="3" />
        </svg>
        <div>
          <div className="font-semibold">{t("ticket")}</div>
          <div className="text-sm text-muted-foreground">{t("candidate")}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
      <svg className="h-12 w-12 text-foreground" viewBox="0 0 48 48" fill="none" aria-hidden="true">
        <rect x="8" y="9" width="32" height="30" rx="7" fill="currentColor" />
        <path d="M16 31V21M24 31V15M32 31V24" stroke="white" strokeWidth="4" strokeLinecap="round" />
      </svg>
      <div>
        <div className="font-semibold">{t("bars")}</div>
        <div className="text-sm text-muted-foreground">{t("candidate")}</div>
      </div>
    </div>
  );
}
