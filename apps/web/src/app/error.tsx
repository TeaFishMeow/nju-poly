"use client";

import { useTranslations } from "next-intl";

import { SiteShell } from "@/components/site-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ErrorPage({ reset }: { reset: () => void }) {
  const t = useTranslations("common");

  return (
    <SiteShell>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("errorTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm leading-6 text-muted-foreground">{t("errorDescription")}</p>
            <Button onClick={reset}>{t("retry")}</Button>
          </CardContent>
        </Card>
      </main>
    </SiteShell>
  );
}
