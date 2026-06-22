import { BuyControl } from "@/components/buy-control";
import { EventFormPreview } from "@/components/form-preview";
import { LogoCandidate } from "@/components/brand-logo";
import { MarketCard } from "@/components/market-card";
import { ProbabilityBar } from "@/components/probability-bar";
import { SiteShell } from "@/components/site-shell";
import { EmptyState, ErrorState, LoadingState } from "@/components/state-panels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ToastPreview } from "@/components/ui/toast";
import { getDictionary } from "@/i18n/server";
import { logoPrompts } from "@/lib/brand-prompts";

const swatches = [
  { name: "Ink", className: "bg-foreground" },
  { name: "Market teal", className: "bg-primary" },
  { name: "Campus blue", className: "bg-accent" },
  { name: "YES", className: "bg-yes" },
  { name: "NO", className: "bg-no" },
  { name: "Notice", className: "bg-warning" },
];

export default async function DesignPage() {
  const { t } = await getDictionary();

  return (
    <SiteShell>
      <main className="mx-auto max-w-7xl space-y-8 px-4 py-6 sm:px-6">
        <section className="rounded-lg border bg-card p-6 shadow-surface">
          <Badge variant="outline">{t("design.badge")}</Badge>
          <h1 className="mt-3 font-display text-3xl font-semibold sm:text-4xl">{t("design.title")}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            {t("design.description")}
          </p>
        </section>

        <section className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
          <Card>
            <CardHeader>
              <CardTitle>{t("design.colorTokens")}</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {swatches.map((swatch) => (
                <div key={swatch.name} className="flex items-center gap-3">
                  <div className={`h-9 w-12 rounded-md border ${swatch.className}`} />
                  <div className="text-sm font-semibold">{swatch.name}</div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("design.typographyButtons")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <div className="font-display text-3xl font-semibold">南哪竞猜 NJUPoly</div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {t("design.typographyNote")}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button>{t("design.primaryAction")}</Button>
                <Button variant="secondary">{t("design.secondaryAction")}</Button>
                <Button variant="outline">{t("design.outlineAction")}</Button>
                <Button variant="yes">YES</Button>
                <Button variant="no">NO</Button>
                <Button variant="destructive">{t("design.destructiveAction")}</Button>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <LogoCandidate variant="gate" selected />
          <LogoCandidate variant="ticket" />
          <LogoCandidate variant="bars" />
        </section>

        <Card>
          <CardHeader>
            <CardTitle>{t("design.logoPrompts")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {logoPrompts.map((prompt) => (
              <div key={prompt} className="rounded-md bg-muted p-3 font-mono text-xs text-muted-foreground">
                {prompt}
              </div>
            ))}
          </CardContent>
        </Card>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-4">
            <MarketCard
              slug="canteen-window"
              title={t("design.sampleTitleOne")}
              category={t("design.sampleCategoryOne")}
              yes={63}
              volume="128.40 NWC"
              closeLabel={t("design.sampleCloseOne")}
            />
            <MarketCard
              slug="grass-concert-weather"
              title={t("design.sampleTitleTwo")}
              category={t("design.sampleCategoryTwo")}
              yes={38}
              volume="83.20 NWC"
              closeLabel={t("design.sampleCloseTwo")}
            />
            <Card>
              <CardHeader>
                <CardTitle>{t("design.oddsTitle")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ProbabilityBar yes={72} />
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div className="rounded-md bg-muted p-3">
                    <div className="text-muted-foreground">YES</div>
                    <div className="font-mono font-semibold">72%</div>
                  </div>
                  <div className="rounded-md bg-muted p-3">
                    <div className="text-muted-foreground">NO</div>
                    <div className="font-mono font-semibold">28%</div>
                  </div>
                  <div className="rounded-md bg-muted p-3">
                    <div className="text-muted-foreground">Pool</div>
                    <div className="font-mono font-semibold">211.60</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <BuyControl />
            <EventFormPreview />
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <EmptyState />
          <LoadingState />
          <ErrorState />
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <ToastPreview tone="success" title={t("design.toastSuccessTitle")} description={t("design.toastSuccessDescription")} />
          <ToastPreview tone="info" title={t("design.toastInfoTitle")} description={t("design.toastInfoDescription")} />
          <ToastPreview tone="error" title={t("design.toastErrorTitle")} description={t("design.toastErrorDescription")} />
        </section>
      </main>
    </SiteShell>
  );
}
