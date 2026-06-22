import Link from "next/link";

import { SiteShell } from "@/components/site-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDictionary } from "@/i18n/server";

export default async function NotFound() {
  const { t } = await getDictionary();

  return (
    <SiteShell>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("common.notFoundTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm leading-6 text-muted-foreground">{t("common.notFoundDescription")}</p>
            <Button asChild>
              <Link href="/">{t("common.backHome")}</Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    </SiteShell>
  );
}
