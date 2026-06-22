"use client";

import { useState } from "react";
import { Scale } from "lucide-react";
import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiJson } from "@/lib/api";

type AppealPanelProps = {
  marketSlug: string;
  status: string;
  proposedResult: string | null;
  appealWindowEndsAt: string | null;
};

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function AppealPanel({ marketSlug, status, proposedResult, appealWindowEndsAt }: AppealPanelProps) {
  const t = useTranslations("appealPanel");
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const isResolving = status === "resolving";
  const windowLabel = appealWindowEndsAt ? new Date(appealWindowEndsAt).toLocaleString() : t("notInWindow");

  async function submitAppeal() {
    const token = localStorage.getItem("njupoly_token");
    if (!token) {
      setError(t("needLogin"));
      return;
    }
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      await apiJson(`/markets/${marketSlug}/appeals`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ reason }),
      });
      setReason("");
      setNotice(t("submitted"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" aria-hidden="true" />
          {t("title")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Badge variant={isResolving ? "warning" : "outline"}>{isResolving ? t("open") : t("closed")}</Badge>
          {proposedResult ? <Badge variant={proposedResult === "YES" ? "yes" : "no"}>{t("currentResult", { result: proposedResult })}</Badge> : null}
        </div>
        <div className="rounded-md bg-muted p-3 text-xs text-muted-foreground">{t("endsAt", { time: windowLabel })}</div>
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder={t("placeholder")}
          disabled={!isResolving || submitting}
          className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        {notice ? <div className="rounded-md border border-yes/30 bg-yes/10 p-3 text-sm text-yes">{notice}</div> : null}
        {error ? <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        <Button className="w-full" onClick={submitAppeal} disabled={!isResolving || !reason.trim() || submitting}>
          {t("submit")}
        </Button>
      </CardContent>
    </Card>
  );
}
