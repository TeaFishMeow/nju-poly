"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Minus, Plus } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiJson } from "@/lib/api";

export function BuyControl({
  marketSlug,
  yes = 50,
  balance,
}: {
  marketSlug?: string;
  yes?: number;
  balance?: string;
}) {
  const router = useRouter();
  const t = useTranslations("trade");
  const [amount, setAmount] = useState("1.00");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const no = 100 - yes;

  function step(delta: number) {
    const next = Math.max(0.01, Number(amount || 0) + delta);
    setAmount(next.toFixed(2));
  }

  async function buy(side: "YES" | "NO") {
    if (!marketSlug) {
      return;
    }
    const token = localStorage.getItem("njupoly_token");
    if (!token) {
      setError(t("signInRequired"));
      return;
    }
    const amountCents = Math.round(Number(amount) * 100);
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      await apiJson(`/markets/${marketSlug}/bets`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ side, amount_cents: amountCents }),
      });
      setMessage(t("success", { side, amount }));
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="grid grid-cols-2 gap-2">
        <Button variant="yes" onClick={() => buy("YES")} disabled={loading || !marketSlug}>
          {t("buyYes", { yes })}
        </Button>
        <Button variant="no" onClick={() => buy("NO")} disabled={loading || !marketSlug}>
          {t("buyNo", { no })}
        </Button>
      </div>

      <div className="mt-4 space-y-2">
        <Label htmlFor="stake">{t("amount")}</Label>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" aria-label={t("decrease")} onClick={() => step(-1)}>
            <Minus className="h-4 w-4" aria-hidden="true" />
          </Button>
          <Input
            id="stake"
            inputMode="decimal"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            className="text-center font-mono"
          />
          <Button variant="outline" size="icon" aria-label={t("increase")} onClick={() => step(1)}>
            <Plus className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 rounded-md bg-muted p-3 text-sm">
        <div>
          <div className="text-muted-foreground">{t("stake")}</div>
          <div className="font-mono font-semibold">{amount || "0.00"} NWC</div>
        </div>
        <div>
          <div className="text-muted-foreground">{t("balance")}</div>
          <div className="font-mono font-semibold">{balance ?? t("signedOutBalance")}</div>
        </div>
      </div>
      {message ? <div className="mt-3 rounded-md bg-yes/10 p-3 text-sm text-yes">{message}</div> : null}
      {error ? <div className="mt-3 rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
    </div>
  );
}
