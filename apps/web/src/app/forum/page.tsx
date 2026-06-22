import Link from "next/link";
import { MessageCircle, PenLine } from "lucide-react";

import { ForumPostComposer } from "@/components/forum-composer";
import { SiteShell } from "@/components/site-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDictionary } from "@/i18n/server";
import { apiJson } from "@/lib/api";

export const dynamic = "force-dynamic";

type ForumPost = {
  slug: string;
  title: string;
  excerpt: string;
  author_student_id: string;
  replies: number;
  updated_at: string;
};

type ForumPostListResponse = {
  posts: ForumPost[];
};

export default async function ForumPage() {
  const { t } = await getDictionary();
  const forum = await apiJson<ForumPostListResponse>("/forum", { cache: "no-store" });

  return (
    <SiteShell>
      <main className="mx-auto max-w-5xl space-y-5 px-4 py-6 sm:px-6">
        <section className="flex flex-col gap-4 rounded-lg border bg-card p-5 shadow-surface sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Badge variant="outline">{t("forum.badge")}</Badge>
            <h1 className="mt-3 font-display text-3xl font-semibold">{t("forum.title")}</h1>
          </div>
          <Button>
            <PenLine className="h-4 w-4" aria-hidden="true" />
            {t("forum.newPost")}
          </Button>
        </section>

        <ForumPostComposer />

        <div className="grid gap-3">
          {forum.posts.length > 0 ? (
            forum.posts.map((post) => (
              <Card key={post.slug} className="transition-colors hover:border-primary/45">
                <CardContent className="p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <Link href={`/forum/${post.slug}`} className="text-lg font-semibold hover:text-primary">
                        {post.title}
                      </Link>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">{post.excerpt}</p>
                      <div className="mt-3 text-xs text-muted-foreground">
                        {post.author_student_id} · {new Date(post.updated_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-3 font-mono text-sm text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <MessageCircle className="h-4 w-4" aria-hidden="true" />
                        {post.replies}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="p-4 text-sm text-muted-foreground">{t("forum.empty")}</CardContent>
            </Card>
          )}
        </div>
      </main>
    </SiteShell>
  );
}
