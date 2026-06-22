"use client";

import { Languages } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";

import { localeCookieName, type Locale } from "@/i18n/messages";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LocaleToggle({ className }: { className?: string }) {
  const router = useRouter();
  const locale = useLocale() as Locale;
  const t = useTranslations("shell");
  const nextLocale: Locale = locale === "zh" ? "en" : "zh";

  function switchLocale() {
    document.cookie = `${localeCookieName}=${nextLocale}; path=/; max-age=31536000; samesite=lax`;
    document.documentElement.lang = nextLocale === "zh" ? "zh-CN" : "en";
    router.refresh();
  }

  return (
    <Button variant="outline" size="sm" aria-label={t("toggleLocale")} onClick={switchLocale} className={cn(className)}>
      <Languages className="h-4 w-4" aria-hidden="true" />
      <span className="hidden sm:inline">{t("localeLabel")}</span>
    </Button>
  );
}
