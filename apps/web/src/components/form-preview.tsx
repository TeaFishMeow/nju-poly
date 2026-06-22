"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function EventFormPreview() {
  const t = useTranslations("design.formPreview");

  return (
    <form className="space-y-4 rounded-lg border bg-card p-4">
      <div className="space-y-2">
        <Label htmlFor="title">{t("title")}</Label>
        <Input id="title" defaultValue={t("defaultTitle")} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="category">{t("category")}</Label>
          <Input id="category" defaultValue={t("defaultCategory")} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="close">{t("closeTime")}</Label>
          <Input id="close" defaultValue="2026-06-30 20:00" />
        </div>
      </div>
      <Button type="button">{t("submit")}</Button>
    </form>
  );
}
