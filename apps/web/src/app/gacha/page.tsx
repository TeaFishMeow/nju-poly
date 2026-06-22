import { Sparkles } from "lucide-react";

import { SiteShell } from "@/components/site-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDictionary } from "@/i18n/server";

export default async function GachaPage() {
  const { dictionary, t } = await getDictionary();

  return (
    <SiteShell>
      <main className="mx-auto max-w-5xl space-y-5 px-4 py-6 sm:px-6">
        <section className="rounded-lg border bg-card p-6 shadow-surface">
          <Badge variant="warning">{t("gacha.badge")}</Badge>
          <h1 className="mt-3 font-display text-3xl font-semibold">{t("gacha.title")}</h1>
          <p className="mt-3 max-w-2xl leading-7 text-muted-foreground">
            {t("gacha.description")}
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {dictionary.gacha.items.map((item) => (
            <Card key={item}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-warning" aria-hidden="true" />
                  {item}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex aspect-square items-center justify-center rounded-lg border bg-muted">
                  <Sparkles className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
                </div>
                <Button className="mt-4 w-full" disabled>
                  {t("gacha.unavailable")}
                </Button>
              </CardContent>
            </Card>
          ))}
        </section>
      </main>
    </SiteShell>
  );
}
