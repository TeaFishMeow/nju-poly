"use client";

import { useState } from "react";
import { PenLine, Send } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiJson } from "@/lib/api";

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

export function ForumPostComposer() {
  const t = useTranslations("forum");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [posting, setPosting] = useState(false);

  async function submitPost() {
    const token = localStorage.getItem("njupoly_token");
    if (!token) {
      setError(t("needLoginPost"));
      return;
    }
    setPosting(true);
    setError(null);
    try {
      const slugBase = slugify(title) || "post";
      const post = await apiJson<{ slug: string }>("/forum", {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({
          slug: `${slugBase}-${Date.now().toString(36)}`,
          title,
          body,
        }),
      });
      window.location.href = `/forum/${post.slug}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : t("postError"));
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="grid gap-3 rounded-lg border bg-card p-4 shadow-surface">
      <div className="flex items-center gap-2 font-semibold">
        <PenLine className="h-4 w-4 text-primary" aria-hidden="true" />
        {t("newPost")}
      </div>
      <div className="grid gap-2">
        <Label htmlFor="forum-title">{t("postTitle")}</Label>
        <Input id="forum-title" value={title} onChange={(event) => setTitle(event.target.value)} placeholder={t("postTitlePlaceholder")} />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="forum-body">{t("postBody")}</Label>
        <textarea
          id="forum-body"
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder={t("postBodyPlaceholder")}
          className="min-h-28 rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>
      {error ? <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
      <Button onClick={submitPost} disabled={!title.trim() || !body.trim() || posting}>
        <Send className="h-4 w-4" aria-hidden="true" />
        {t("publish")}
      </Button>
    </div>
  );
}

export function ForumReplyComposer({ slug }: { slug: string }) {
  const t = useTranslations("forum");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [posting, setPosting] = useState(false);

  async function submitReply() {
    const token = localStorage.getItem("njupoly_token");
    if (!token) {
      setError(t("needLoginReply"));
      return;
    }
    setPosting(true);
    setError(null);
    try {
      await apiJson(`/forum/${slug}/replies`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ body }),
      });
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("replyError"));
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="space-y-3">
      <textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        placeholder={t("replyPlaceholder")}
        className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      {error ? <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
      <Button onClick={submitReply} disabled={!body.trim() || posting}>
        <Send className="h-4 w-4" aria-hidden="true" />
        {t("send")}
      </Button>
    </div>
  );
}
