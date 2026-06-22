"use client";

import { Loader2, SearchX, TriangleAlert } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export function EmptyState() {
  const t = useTranslations("common");

  return (
    <div className="rounded-lg border bg-card p-6 text-center">
      <SearchX className="mx-auto h-7 w-7 text-muted-foreground" aria-hidden="true" />
      <h3 className="mt-3 font-semibold">{t("emptyStateTitle")}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{t("emptyStateDescription")}</p>
      <Button className="mt-4" size="sm">{t("emptyStateAction")}</Button>
    </div>
  );
}

export function LoadingState() {
  const t = useTranslations("common");

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4 text-sm font-medium">
      <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden="true" />
      {t("loadingState")}
    </div>
  );
}

export function ErrorState() {
  const t = useTranslations("common");

  return (
    <div className="rounded-lg border border-destructive/35 bg-destructive/10 p-4">
      <div className="flex items-center gap-2 font-semibold">
        <TriangleAlert className="h-4 w-4 text-destructive" aria-hidden="true" />
        {t("errorStateTitle")}
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{t("errorStateDescription")}</p>
    </div>
  );
}
