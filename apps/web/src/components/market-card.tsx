"use client";

import Link from "next/link";
import { ArrowUpRight, Clock3 } from "lucide-react";
import { useTranslations } from "next-intl";

import { ProbabilityBar } from "@/components/probability-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export type MarketCardProps = {
  slug: string;
  title: string;
  category: string;
  yes: number;
  volume: string;
  closeLabel: string;
};

export function MarketCard({ slug, title, category, yes, volume, closeLabel }: MarketCardProps) {
  const t = useTranslations("common");

  return (
    <Card className="overflow-hidden transition-colors hover:border-primary/45">
      <CardContent className="grid min-w-0 gap-4 p-4 sm:grid-cols-[minmax(0,1fr)_236px] sm:items-center">
        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Badge>{category}</Badge>
            <span className="font-mono text-xs font-semibold text-muted-foreground">{volume}</span>
            <span className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <Clock3 className="h-3.5 w-3.5" aria-hidden="true" />
              {closeLabel}
            </span>
          </div>
          <h2 className="text-base font-semibold leading-snug">{title}</h2>
          <ProbabilityBar yes={yes} className="mt-4 max-w-md" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Button variant="yes">YES {yes}%</Button>
          <Button variant="no">NO {100 - yes}%</Button>
          <Button asChild variant="outline" className="col-span-2">
            <Link href={`/markets/${slug}`}>
              {t("viewMarket")}
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
