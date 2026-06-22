import { Filter, Search } from "lucide-react";
import Link from "next/link";

import { MarketCard } from "@/components/market-card";
import { SiteShell } from "@/components/site-shell";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getDictionary } from "@/i18n/server";
import { apiJson } from "@/lib/api";

export const dynamic = "force-dynamic";

type Market = {
  slug: string;
  title: string;
  category: string;
  yes: number;
  volume: string;
  closeLabel: string;
};

type MarketListResponse = {
  markets: Market[];
  categories: string[];
};

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<{
    category?: string;
  }>;
}) {
  const { t } = await getDictionary();
  const resolvedSearchParams = await searchParams;
  const selectedCategory = resolvedSearchParams?.category ?? "全部";
  const data = await apiJson<MarketListResponse>(
    selectedCategory === "全部" ? "/markets" : `/markets?category=${encodeURIComponent(selectedCategory)}`,
    { cache: "no-store" },
  );
  const totalVolumeCents = data.markets.reduce((sum, market) => {
    const numeric = Number(market.volume.replace(" NWC", ""));
    return sum + Math.round(numeric * 100);
  }, 0);
  const displayCategory = (category: string) => (category === "全部" ? t("home.allCategory") : category);

  return (
    <SiteShell>
      <main>
        <section className="mx-auto w-full max-w-7xl space-y-5 overflow-hidden px-4 py-6 sm:px-6">
          <div className="grid min-w-0 gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
            <div className="min-w-0 rounded-lg border bg-card p-5 shadow-surface">
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{t("home.badgeCampus")}</Badge>
                <Badge variant="yes">{t("home.badgeZeroFee")}</Badge>
                <Badge variant="secondary">{t("home.badgeNwc")}</Badge>
              </div>
              <h1 className="mt-3 max-w-80 break-words font-display text-2xl font-semibold leading-tight tracking-normal sm:max-w-3xl sm:text-4xl">
                {t("home.title")}
              </h1>
              <p className="mt-3 max-w-72 break-words text-sm leading-6 text-muted-foreground sm:max-w-2xl">
                {t("home.description")}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button asChild>
                  <Link href="/login">{t("home.login")}</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/dashboard">{t("home.dashboard")}</Link>
                </Button>
              </div>
            </div>

            <div className="grid min-w-0 gap-3 sm:grid-cols-2">
              <StatCard label={t("home.totalPool")} value={(totalVolumeCents / 100).toFixed(2)} hint={t("home.totalPoolHint")} />
              <StatCard label={t("home.openMarkets")} value={String(data.markets.length)} hint={t("home.openMarketsHint")} />
              <StatCard label={t("home.dailyCheckIn")} value="+1.00" hint={t("home.dailyCheckInHint")} />
              <StatCard label={t("home.activeDiscussion")} value="28" hint={t("home.activeDiscussionHint")} />
            </div>
          </div>

          <div className="min-w-0 rounded-lg border bg-card p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex min-w-0 items-center gap-2 rounded-md border bg-background px-3 py-2 lg:w-96">
                <Search className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                <Input className="h-6 border-0 bg-transparent p-0 focus-visible:ring-0" placeholder={t("home.searchPlaceholder")} />
              </div>
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                <Filter className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                {data.categories.map((category) => (
                  <Button
                    key={category}
                    asChild
                    size="sm"
                    variant={selectedCategory === category ? "default" : "outline"}
                    className="shrink-0"
                  >
                    <a href={category === "全部" ? "/" : `/?category=${encodeURIComponent(category)}`}>{displayCategory(category)}</a>
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-3">
            {data.markets.length > 0 ? (
              data.markets.map((market) => <MarketCard key={market.slug} {...market} category={displayCategory(market.category)} />)
            ) : (
              <div className="rounded-lg border bg-card p-4 text-sm text-muted-foreground">{t("home.emptyMarkets")}</div>
            )}
          </div>
        </section>
      </main>
    </SiteShell>
  );
}
