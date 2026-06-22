import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, CalendarClock, Users } from "lucide-react";

import { AppealPanel } from "@/components/appeal-panel";
import { BuyControl } from "@/components/buy-control";
import { ProbabilityBar } from "@/components/probability-bar";
import { SiteShell } from "@/components/site-shell";
import { TrendChart } from "@/components/trend-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDictionary } from "@/i18n/server";
import { apiJson } from "@/lib/api";

export const dynamic = "force-dynamic";

type Market = {
  slug: string;
  title: string;
  description: string;
  criteria: string;
  category: string;
  status: string;
  proposed_result: string | null;
  appeal_window_ends_at: string | null;
  yes: number;
  no: number;
  volume: string;
  close_time: string;
  participants: number;
  trend: number[];
};

type MarketListResponse = {
  markets: Market[];
  categories: string[];
};

async function readMarket(slug: string) {
  try {
    return await apiJson<Market>(`/markets/${slug}`, { cache: "no-store" });
  } catch {
    notFound();
  }
}

export default async function MarketDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { t } = await getDictionary();
  const { slug } = await params;
  const market = await readMarket(slug);
  const related = await apiJson<MarketListResponse>(`/markets?category=${encodeURIComponent(market.category)}`, { cache: "no-store" });
  const relatedMarkets = related.markets.filter((item) => item.slug !== market.slug).slice(0, 2);

  return (
    <SiteShell>
      <main className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
        <Button asChild variant="ghost" size="sm">
          <Link href="/">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t("common.backHome")}
          </Link>
        </Button>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-5">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>{market.category}</Badge>
                  <Badge variant="outline">{market.status}</Badge>
                  <span className="font-mono text-xs font-semibold text-muted-foreground">{market.volume}</span>
                </div>
                <CardTitle className="font-display text-3xl leading-tight">{market.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <p className="leading-7 text-muted-foreground">{market.description}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-md bg-muted p-3">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <CalendarClock className="h-4 w-4 text-primary" aria-hidden="true" />
                      {t("market.closeTime")}
                    </div>
                    <div className="mt-2 font-mono text-sm">{new Date(market.close_time).toLocaleString()}</div>
                  </div>
                  <div className="rounded-md bg-muted p-3">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <Users className="h-4 w-4 text-primary" aria-hidden="true" />
                      {t("market.participants")}
                    </div>
                    <div className="mt-2 font-mono text-sm">{market.participants}</div>
                  </div>
                </div>
                <ProbabilityBar yes={market.yes} />
              </CardContent>
            </Card>

            <TrendChart values={market.trend} />

            <Card>
              <CardHeader>
                <CardTitle>{t("market.criteria")}</CardTitle>
              </CardHeader>
              <CardContent className="leading-7 text-muted-foreground">{market.criteria}</CardContent>
            </Card>
          </div>

          <aside className="space-y-5">
            <BuyControl marketSlug={market.slug} yes={market.yes} />
            <AppealPanel
              marketSlug={market.slug}
              status={market.status}
              proposedResult={market.proposed_result}
              appealWindowEndsAt={market.appeal_window_ends_at}
            />
            <Card>
              <CardHeader>
                <CardTitle>{t("market.related")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {relatedMarkets.length > 0 ? (
                  relatedMarkets.map((item) => (
                    <Link
                      key={item.slug}
                      href={`/markets/${item.slug}`}
                      className="block rounded-md border bg-background p-3 transition-colors hover:border-primary/45"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0 font-semibold">{item.title}</div>
                        <Badge variant={item.yes >= 50 ? "yes" : "no"}>{item.yes}%</Badge>
                      </div>
                      <div className="mt-2 font-mono text-xs text-muted-foreground">{item.volume}</div>
                    </Link>
                  ))
                ) : (
                  <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("market.noRelated")}</div>
                )}
              </CardContent>
            </Card>
          </aside>
        </section>
      </main>
    </SiteShell>
  );
}
