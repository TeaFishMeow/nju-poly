import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Send } from "lucide-react";

import { ForumReplyComposer } from "@/components/forum-composer";
import { SiteShell } from "@/components/site-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDictionary } from "@/i18n/server";
import { apiJson } from "@/lib/api";

export const dynamic = "force-dynamic";

type ForumReply = {
  id: number;
  body: string;
  author_id_hash: string;
  created_at: string;
};

type ForumPostDetail = {
  slug: string;
  title: string;
  body: string;
  author_id_hash: string;
  created_at: string;
  reply_items: ForumReply[];
};

async function readPost(slug: string) {
  try {
    return await apiJson<ForumPostDetail>(`/forum/${slug}`, { cache: "no-store" });
  } catch {
    notFound();
  }
}

export default async function ForumPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { t } = await getDictionary();
  const { slug } = await params;
  const post = await readPost(slug);

  return (
    <SiteShell>
      <main className="mx-auto max-w-4xl space-y-5 px-4 py-6 sm:px-6">
        <Button asChild variant="ghost" size="sm">
          <Link href="/forum">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t("common.backForum")}
          </Link>
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="font-display text-3xl leading-tight">{post.title}</CardTitle>
            <div className="text-sm text-muted-foreground">{post.author_id_hash} · {new Date(post.created_at).toLocaleString()}</div>
          </CardHeader>
          <CardContent className="space-y-5">
            <p className="whitespace-pre-wrap leading-7 text-muted-foreground">{post.body}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("forum.replies")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {post.reply_items.length > 0 ? (
              post.reply_items.map((reply) => (
                <div key={reply.id} className="rounded-md bg-muted p-3">
                  <div className="text-sm font-semibold">{reply.author_id_hash}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{new Date(reply.created_at).toLocaleString()}</div>
                  <div className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{reply.body}</div>
                </div>
              ))
            ) : (
              <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{t("forum.noReplies")}</div>
            )}
            <ForumReplyComposer slug={post.slug} />
          </CardContent>
        </Card>
      </main>
    </SiteShell>
  );
}
