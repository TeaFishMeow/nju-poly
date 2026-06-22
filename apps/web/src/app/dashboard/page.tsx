"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CalendarPlus, CheckCircle2, ClipboardCopy, KeyRound, MessageSquare, Scale, ShieldCheck, Tags, Trash2 } from "lucide-react";
import { useTranslations } from "next-intl";

import { SiteShell } from "@/components/site-shell";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_BASE_URL, apiJson } from "@/lib/api";

type LedgerItem = {
  id: number;
  kind: string;
  ref: string;
  amount: string;
  amount_cents: number;
  created_at: string;
};

type MeResponse = {
  user: {
    student_id: string;
    email: string;
    account_key: string;
    is_admin: boolean;
  };
  balance: string;
  balance_cents: number;
  can_check_in: boolean;
  ledger: LedgerItem[];
};

type Category = {
  name: string;
};

type Market = {
  slug: string;
  title: string;
  category: string;
  status: string;
  close_time: string;
  cover_url: string | null;
};

type MarketListResponse = {
  markets: Market[];
  categories: string[];
};

type Appeal = {
  id: number;
  event_slug: string;
  event_title: string;
  event_status: string;
  proposed_result: "YES" | "NO" | null;
  appeal_window_ends_at: string;
  user_student_id: string;
  reason: string;
  status: string;
  created_at: string;
};

type AppealListResponse = {
  appeals: Appeal[];
};

type ForumReply = {
  id: number;
  body: string;
  author_student_id: string;
  created_at: string;
};

type ForumPost = {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  author_student_id: string;
  replies: number;
  updated_at: string;
};

type ForumPostDetail = ForumPost & {
  body: string;
  reply_items: ForumReply[];
};

type ForumPostListResponse = {
  posts: ForumPost[];
};

type ApiTokenRecord = {
  id: number;
  name: string;
  token_prefix: string;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
};

type ApiTokenListResponse = {
  tokens: ApiTokenRecord[];
};

type ApiTokenCreateResponse = {
  token: string;
  record: ApiTokenRecord;
};

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function slugify(input: string) {
  return input
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const commonT = useTranslations("common");
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<MeResponse | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pendingMarkets, setPendingMarkets] = useState<Market[]>([]);
  const [openMarkets, setOpenMarkets] = useState<Market[]>([]);
  const [pendingAppeals, setPendingAppeals] = useState<Appeal[]>([]);
  const [forumPosts, setForumPosts] = useState<ForumPostDetail[]>([]);
  const [apiTokens, setApiTokens] = useState<ApiTokenRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [eventTitle, setEventTitle] = useState(t("event.defaultTitle"));
  const [eventDescription, setEventDescription] = useState(t("event.defaultDescription"));
  const [eventCriteria, setEventCriteria] = useState(t("event.defaultCriteria"));
  const [eventCategory, setEventCategory] = useState("公告");
  const [eventCloseTime, setEventCloseTime] = useState("2030-01-01T20:00");
  const [newCategory, setNewCategory] = useState("");
  const [settlementSlug, setSettlementSlug] = useState("");
  const [settlementResult, setSettlementResult] = useState<"YES" | "NO">("YES");
  const [transferStudentId, setTransferStudentId] = useState("");
  const [transferAmount, setTransferAmount] = useState("1.00");
  const [apiTokenName, setApiTokenName] = useState("local bot");
  const [newApiToken, setNewApiToken] = useState<string | null>(null);

  const categoryNames = useMemo(() => categories.map((category) => category.name), [categories]);

  async function loadCommon() {
    const [categoryResult, marketsResult] = await Promise.all([
      apiJson<Category[]>("/markets/categories"),
      apiJson<MarketListResponse>("/markets"),
    ]);
    setCategories(categoryResult);
    setOpenMarkets(marketsResult.markets);
    if (!categoryResult.some((category) => category.name === eventCategory) && categoryResult[0]) {
      setEventCategory(categoryResult[0].name);
    }
  }

  async function loadDashboard(currentToken: string) {
    setLoading(true);
    setError(null);
    try {
      const result = await apiJson<MeResponse>("/auth/me", { headers: authHeaders(currentToken) });
      setData(result);
      await loadCommon();
      const tokens = await apiJson<ApiTokenListResponse>("/auth/api-tokens", { headers: authHeaders(currentToken) });
      setApiTokens(tokens.tokens);
      if (result.user.is_admin) {
        const pending = await apiJson<MarketListResponse>("/markets/pending", { headers: authHeaders(currentToken) });
        setPendingMarkets(pending.markets);
        const appeals = await apiJson<AppealListResponse>("/markets/appeals/pending", { headers: authHeaders(currentToken) });
        setPendingAppeals(appeals.appeals);
        const forum = await apiJson<ForumPostListResponse>("/forum", { cache: "no-store" });
        const details = await Promise.all(
          forum.posts.slice(0, 10).map((post) => apiJson<ForumPostDetail>(`/forum/${post.slug}`, { cache: "no-store" }))
        );
        setForumPosts(details);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("readError"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const storedToken = localStorage.getItem("njupoly_token");
    setToken(storedToken);
    void loadCommon().catch((err) => setError(err instanceof Error ? err.message : t("categoryError")));
    if (storedToken) {
      void loadDashboard(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  async function handleCheckIn() {
    if (!token) return;
    setCheckingIn(true);
    setError(null);
    try {
      await apiJson("/auth/check-in", {
        method: "POST",
        headers: authHeaders(token),
      });
      await loadDashboard(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("checkInError"));
    } finally {
      setCheckingIn(false);
    }
  }

  async function submitEvent() {
    if (!token) {
      setError(t("needLoginEvent"));
      return;
    }
    setError(null);
    setNotice(null);
    const slugBase = slugify(eventTitle) || "event";
    try {
      await apiJson("/markets", {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({
          slug: `${slugBase}-${Date.now().toString(36)}`,
          title: eventTitle,
          description: eventDescription,
          criteria: eventCriteria,
          category: eventCategory,
          close_time: new Date(eventCloseTime).toISOString(),
        }),
      });
      setNotice(t("eventSubmitted"));
      if (data?.user.is_admin) {
        await loadDashboard(token);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("eventError"));
    }
  }

  async function approveMarket(slug: string) {
    if (!token) return;
    await apiJson(`/markets/${slug}/approve`, { method: "POST", headers: authHeaders(token) });
    await loadDashboard(token);
  }

  async function rejectMarket(slug: string) {
    if (!token) return;
    await apiJson(`/markets/${slug}/reject`, { method: "POST", headers: authHeaders(token) });
    await loadDashboard(token);
  }

  async function addCategory() {
    if (!token || !newCategory.trim()) return;
    await apiJson("/markets/categories", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ name: newCategory.trim() }),
    });
    setNewCategory("");
    await loadCommon();
  }

  async function removeCategory(name: string) {
    if (!token) return;
    await apiJson(`/markets/categories/${encodeURIComponent(name)}`, { method: "DELETE", headers: authHeaders(token) });
    await loadCommon();
  }

  async function closeSelectedMarket() {
    if (!token || !settlementSlug) return;
    await apiJson(`/markets/${settlementSlug}/close`, { method: "POST", headers: authHeaders(token) });
    await loadCommon();
  }

  async function proposeSelectedResult() {
    if (!token || !settlementSlug) return;
    await apiJson(`/markets/${settlementSlug}/propose-result`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ result: settlementResult }),
    });
    await loadCommon();
  }

  async function settleSelectedMarket() {
    if (!token || !settlementSlug) return;
    await apiJson(`/markets/${settlementSlug}/settle`, { method: "POST", headers: authHeaders(token) });
    await loadCommon();
  }

  async function deleteAndRefundSelectedMarket() {
    if (!token || !settlementSlug) return;
    if (!window.confirm("Delete this event and refund all bought tokens?")) return;
    await apiJson(`/markets/${settlementSlug}`, { method: "DELETE", headers: authHeaders(token) });
    setSettlementSlug("");
    await loadDashboard(token);
  }

  async function submitTransfer() {
    if (!token) return;
    setError(null);
    setNotice(null);
    const amount_cents = Math.round(Number(transferAmount) * 100);
    if (!transferStudentId.trim() || !Number.isInteger(amount_cents) || amount_cents <= 0) {
      setError(t("transferInvalid"));
      return;
    }
    try {
      await apiJson("/auth/transfers", {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ to_student_id: transferStudentId.trim(), amount_cents }),
      });
      setNotice(t("transferDone"));
      setTransferAmount("1.00");
      await loadDashboard(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("transferError"));
    }
  }

  async function createApiToken() {
    if (!token || !apiTokenName.trim()) return;
    setError(null);
    setNotice(null);
    try {
      const result = await apiJson<ApiTokenCreateResponse>("/auth/api-tokens", {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ name: apiTokenName.trim() }),
      });
      setNewApiToken(result.token);
      setApiTokens((current) => [result.record, ...current]);
      setNotice(t("tokenCreated"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("tokenError"));
    }
  }

  async function revokeApiToken(tokenId: number) {
    if (!token) return;
    setError(null);
    try {
      const result = await apiJson<ApiTokenRecord>(`/auth/api-tokens/${tokenId}`, {
        method: "DELETE",
        headers: authHeaders(token),
      });
      setApiTokens((current) => current.map((item) => (item.id === tokenId ? result : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("revokeError"));
    }
  }

  async function copyNewApiToken() {
    if (!newApiToken) return;
    await navigator.clipboard.writeText(newApiToken);
    setNotice(t("tokenCopied"));
  }

  async function supportAppeal(appeal: Appeal) {
    if (!token || !appeal.proposed_result) return;
    const nextResult = appeal.proposed_result === "YES" ? "NO" : "YES";
    await apiJson(`/markets/appeals/${appeal.id}/support`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ result: nextResult }),
    });
    await loadDashboard(token);
  }

  async function rejectAppeal(appeal: Appeal) {
    if (!token) return;
    await apiJson(`/markets/appeals/${appeal.id}/reject`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({}),
    });
    await loadDashboard(token);
  }

  async function deleteForumPost(slug: string) {
    if (!token) return;
    if (!window.confirm("Delete this post and all of its replies?")) return;
    await apiJson(`/forum/${slug}`, { method: "DELETE", headers: authHeaders(token) });
    await loadDashboard(token);
  }

  async function deleteForumReply(slug: string, replyId: number) {
    if (!token) return;
    await apiJson(`/forum/${slug}/replies/${replyId}`, { method: "DELETE", headers: authHeaders(token) });
    await loadDashboard(token);
  }

  const accountKey = data?.user.account_key ?? t("signedOut");
  const balanceValue = data ? data.balance.replace(" NWC", "") : loading ? "..." : "0.00";
  const adminValue = data?.user.is_admin ? t("stats.adminYes") : t("stats.adminNo");
  const ledgerItems = data?.ledger ?? [];
  const selectedSettlementMarket = openMarkets.find((market) => market.slug === settlementSlug);
  const selectedMarketCanBeDeleted =
    Boolean(data?.user.is_admin) &&
    selectedSettlementMarket?.status === "open" &&
    new Date(selectedSettlementMarket.close_time).getTime() > Date.now();

  return (
    <SiteShell>
      <main className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="rounded-lg border bg-card p-5 shadow-surface">
            <Badge variant="outline">{accountKey}</Badge>
            <h1 className="mt-3 font-display text-3xl font-semibold">{t("title")}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("description")}
            </p>
            {!token ? (
              <Button asChild className="mt-4">
                <Link href="/login">{t("login")}</Link>
              </Button>
            ) : null}
            {notice ? <div className="mt-4 rounded-md border border-yes/30 bg-yes/10 p-3 text-sm text-yes">{notice}</div> : null}
            {error ? <div className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label={t("stats.balance")} value={balanceValue} hint="NWC" />
            <StatCard label={t("stats.pendingMarkets")} value={String(pendingMarkets.length)} hint={t("stats.pendingMarketsHint")} />
            <StatCard label={t("stats.openMarkets")} value={String(openMarkets.length)} hint={t("stats.openMarketsHint")} />
            <StatCard label={t("stats.appeals")} value={String(pendingAppeals.length)} hint={t("stats.appealsHint")} />
            <StatCard label={t("stats.admin")} value={adminValue} hint={data?.user.is_admin ? t("stats.adminHintYes") : t("stats.adminHintNo")} />
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarPlus className="h-4 w-4 text-primary" aria-hidden="true" />
                  {t("event.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3">
                <div className="grid gap-2">
                  <Label htmlFor="event-title">{t("event.eventTitle")}</Label>
                  <Input id="event-title" value={eventTitle} onChange={(event) => setEventTitle(event.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="event-description">{t("event.description")}</Label>
                  <textarea
                    id="event-description"
                    value={eventDescription}
                    onChange={(event) => setEventDescription(event.target.value)}
                    className="min-h-20 rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="event-criteria">{t("event.criteria")}</Label>
                  <textarea
                    id="event-criteria"
                    value={eventCriteria}
                    onChange={(event) => setEventCriteria(event.target.value)}
                    className="min-h-20 rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="grid gap-2">
                    <Label htmlFor="event-category">{t("event.category")}</Label>
                    <select
                      id="event-category"
                      value={eventCategory}
                      onChange={(event) => setEventCategory(event.target.value)}
                      className="h-9 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {categoryNames.map((category) => (
                        <option key={category}>{category}</option>
                      ))}
                    </select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="event-close">{t("event.closeTime")}</Label>
                    <Input id="event-close" type="datetime-local" value={eventCloseTime} onChange={(event) => setEventCloseTime(event.target.value)} />
                  </div>
                </div>
                <Button onClick={submitEvent} disabled={!token}>
                  {t("event.submit")}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("ledger.title")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {ledgerItems.length > 0 ? (
                  ledgerItems.map((item) => (
                    <div key={item.id} className="grid grid-cols-[1fr_auto] gap-3 rounded-md bg-muted p-3 text-sm">
                      <div>
                        <div className="font-semibold">{item.kind}</div>
                        <div className="mt-1 text-muted-foreground">{item.ref} · {new Date(item.created_at).toLocaleString()}</div>
                      </div>
                      <div className={item.amount_cents >= 0 ? "font-mono font-semibold text-yes" : "font-mono font-semibold"}>{item.amount}</div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
                    {loading ? t("ledger.loading") : t("ledger.empty")}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-yes" aria-hidden="true" />
                  {t("checkIn.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{data?.can_check_in ? t("checkIn.available") : t("checkIn.done")}</p>
                <Button className="w-full" onClick={handleCheckIn} disabled={!token || !data?.can_check_in || checkingIn}>
                  {t("checkIn.action")}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ClipboardCopy className="h-4 w-4 text-primary" aria-hidden="true" />
                  {t("transfer.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-2">
                  <Label htmlFor="transfer-student">{t("transfer.student")}</Label>
                  <Input
                    id="transfer-student"
                    value={transferStudentId}
                    onChange={(event) => setTransferStudentId(event.target.value)}
                    placeholder={t("transfer.studentPlaceholder")}
                    disabled={!token}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="transfer-amount">{t("transfer.amount")}</Label>
                  <Input
                    id="transfer-amount"
                    inputMode="decimal"
                    value={transferAmount}
                    onChange={(event) => setTransferAmount(event.target.value)}
                    disabled={!token}
                  />
                </div>
                <Button className="w-full" onClick={submitTransfer} disabled={!token || !transferStudentId.trim()}>
                  {t("transfer.action")}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tags className="h-4 w-4 text-primary" aria-hidden="true" />
                  {t("categories.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input value={newCategory} onChange={(event) => setNewCategory(event.target.value)} placeholder={t("categories.placeholder")} disabled={!data?.user.is_admin} />
                  <Button onClick={addCategory} disabled={!data?.user.is_admin}>
                    {t("categories.add")}
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {categoryNames.map((category) => (
                    <Button key={category} size="sm" variant="outline" onClick={() => removeCategory(category)} disabled={!data?.user.is_admin}>
                      {category}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" aria-hidden="true" />
                  {t("review.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data?.user.is_admin ? (
                  pendingMarkets.length > 0 ? (
                    pendingMarkets.map((item) => (
                      <div key={item.slug} className="rounded-md border bg-background p-3">
                        <div className="font-semibold">{item.title}</div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          {item.category} · {new Date(item.close_time).toLocaleString()}
                        </div>
                        <div className="mt-3 grid grid-cols-2 gap-2">
                          <Button size="sm" onClick={() => approveMarket(item.slug)}>
                            {t("review.approve")}
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => rejectMarket(item.slug)}>
                            {t("review.reject")}
                          </Button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("review.empty")}</div>
                  )
                ) : (
                  <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("review.locked")}</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("settlement.title")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <select
                  value={settlementSlug}
                  onChange={(event) => setSettlementSlug(event.target.value)}
                  disabled={!data?.user.is_admin}
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">{t("settlement.choose")}</option>
                  {openMarkets.map((market) => (
                    <option key={market.slug} value={market.slug}>
                      {market.title}
                    </option>
                  ))}
                </select>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant={settlementResult === "YES" ? "yes" : "outline"} onClick={() => setSettlementResult("YES")} disabled={!data?.user.is_admin}>
                    YES
                  </Button>
                  <Button variant={settlementResult === "NO" ? "no" : "outline"} onClick={() => setSettlementResult("NO")} disabled={!data?.user.is_admin}>
                    NO
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Button size="sm" onClick={closeSelectedMarket} disabled={!data?.user.is_admin || !settlementSlug}>
                    {t("settlement.close")}
                  </Button>
                  <Button size="sm" variant="outline" onClick={proposeSelectedResult} disabled={!data?.user.is_admin || !settlementSlug}>
                    {t("settlement.propose")}
                  </Button>
                  <Button size="sm" variant="outline" onClick={settleSelectedMarket} disabled={!data?.user.is_admin || !settlementSlug}>
                    {t("settlement.settle")}
                  </Button>
                  <Button size="sm" variant="destructive" onClick={deleteAndRefundSelectedMarket} disabled={!selectedMarketCanBeDeleted}>
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                    Delete + refund
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Scale className="h-4 w-4 text-primary" aria-hidden="true" />
                  {t("appeal.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data?.user.is_admin ? (
                  pendingAppeals.length > 0 ? (
                    pendingAppeals.map((appeal) => {
                      const nextResult = appeal.proposed_result === "YES" ? "NO" : "YES";
                      return (
                        <div key={appeal.id} className="rounded-md border bg-background p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="font-semibold">{appeal.event_title}</div>
                              <div className="mt-1 text-xs text-muted-foreground">
                                {appeal.user_student_id} · {new Date(appeal.created_at).toLocaleString()}
                              </div>
                            </div>
                            {appeal.proposed_result ? <Badge variant={appeal.proposed_result === "YES" ? "yes" : "no"}>{appeal.proposed_result}</Badge> : null}
                          </div>
                          <div className="mt-3 rounded-md bg-muted p-3 text-sm leading-6 text-muted-foreground">{appeal.reason}</div>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <Button size="sm" onClick={() => supportAppeal(appeal)} disabled={!appeal.proposed_result}>
                              {t("appeal.changeTo", { result: nextResult })}
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => rejectAppeal(appeal)}>
                              {t("appeal.reject")}
                            </Button>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("appeal.empty")}</div>
                  )
                ) : (
                  <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("appeal.locked")}</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-primary" aria-hidden="true" />
                  Forum moderation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data?.user.is_admin ? (
                  forumPosts.length > 0 ? (
                    forumPosts.map((post) => (
                      <div key={post.slug} className="rounded-md border bg-background p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="font-semibold">{post.title}</div>
                            <div className="mt-1 text-xs text-muted-foreground">
                              {post.author_student_id} · {new Date(post.updated_at).toLocaleString()}
                            </div>
                          </div>
                          <Button size="sm" variant="destructive" onClick={() => deleteForumPost(post.slug)}>
                            <Trash2 className="h-4 w-4" aria-hidden="true" />
                            Delete post
                          </Button>
                        </div>
                        <div className="mt-3 rounded-md bg-muted p-3 text-sm leading-6 text-muted-foreground">{post.excerpt}</div>
                        {post.reply_items.length > 0 ? (
                          <div className="mt-3 space-y-2">
                            {post.reply_items.map((reply) => (
                              <div key={reply.id} className="grid grid-cols-[1fr_auto] gap-2 rounded-md border p-2 text-sm">
                                <div className="min-w-0">
                                  <div className="text-xs text-muted-foreground">
                                    {reply.author_student_id} · {new Date(reply.created_at).toLocaleString()}
                                  </div>
                                  <div className="mt-1 break-words">{reply.body}</div>
                                </div>
                                <Button size="sm" variant="outline" onClick={() => deleteForumReply(post.slug, reply.id)}>
                                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                                  Delete reply
                                </Button>
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))
                  ) : (
                    <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">No forum content yet.</div>
                  )
                ) : (
                  <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">Sign in as an admin to moderate forum content.</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <KeyRound className="h-4 w-4 text-primary" aria-hidden="true" />
                  {t("apiToken.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {newApiToken ? (
                  <div className="space-y-2 rounded-md border border-yes/30 bg-yes/10 p-3">
                    <div className="text-xs font-semibold text-yes">{t("apiToken.oneTime")}</div>
                    <div className="break-all font-mono text-xs">{newApiToken}</div>
                    <Button size="sm" variant="outline" onClick={copyNewApiToken}>
                      <ClipboardCopy className="h-4 w-4" aria-hidden="true" />
                      {t("apiToken.copy")}
                    </Button>
                  </div>
                ) : null}
                <div className="flex gap-2">
                  <Input value={apiTokenName} onChange={(event) => setApiTokenName(event.target.value)} disabled={!token} />
                  <Button onClick={createApiToken} disabled={!token || !apiTokenName.trim()}>
                    {t("apiToken.create")}
                  </Button>
                </div>
                <div className="space-y-2">
                  {apiTokens.length > 0 ? (
                    apiTokens.map((record) => (
                      <div key={record.id} className="rounded-md border bg-background p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <div className="font-semibold">{record.name}</div>
                            <div className="mt-1 font-mono text-xs text-muted-foreground">{record.token_prefix}...</div>
                          </div>
                          <Badge variant={record.revoked_at ? "outline" : "yes"}>{record.revoked_at ? t("apiToken.revoked") : t("apiToken.active")}</Badge>
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          {t("apiToken.created")} {new Date(record.created_at).toLocaleString()}
                          {record.last_used_at ? ` · ${t("apiToken.lastUsed")} ${new Date(record.last_used_at).toLocaleString()}` : ""}
                        </div>
                        <Button className="mt-3" size="sm" variant="destructive" onClick={() => revokeApiToken(record.id)} disabled={Boolean(record.revoked_at)}>
                          {t("apiToken.revoke")}
                        </Button>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("apiToken.empty")}</div>
                  )}
                </div>
                <div className="grid grid-cols-1 gap-2">
                  <Button asChild variant="outline">
                    <Link href={`${API_BASE_URL}/docs`}>
                      <KeyRound className="h-4 w-4" aria-hidden="true" />
                      {commonT("openApiDocs")}
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </aside>
        </section>
      </main>
    </SiteShell>
  );
}
