"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MailCheck, Shield } from "lucide-react";
import { useTranslations } from "next-intl";

import { SiteShell } from "@/components/site-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiJson } from "@/lib/api";

type CodeResponse = {
  email: string;
  delivery: "smtp" | "local_dev";
  dev_code: string | null;
};

type AuthResponse = {
  token: string;
};

export default function LoginPage() {
  const router = useRouter();
  const t = useTranslations("login");
  const [email, setEmail] = useState("251502013@smail.nju.edu.cn");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);
  const [status, setStatus] = useState(t("initialStatus"));
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function requestCode() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiJson<CodeResponse>("/auth/request-code", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setDevCode(result.dev_code);
      setStatus(result.delivery === "smtp" ? t("smtpStatus") : t("localStatus"));
      if (result.dev_code) {
        setCode(result.dev_code);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("requestError"));
    } finally {
      setLoading(false);
    }
  }

  async function verifyCode() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiJson<AuthResponse>("/auth/verify", {
        method: "POST",
        body: JSON.stringify({ email, code }),
      });
      localStorage.setItem("njupoly_token", result.token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("verifyError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <SiteShell>
      <main className="mx-auto grid max-w-5xl gap-5 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <section className="rounded-lg border bg-card p-6 shadow-surface">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <MailCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <h1 className="mt-4 font-display text-3xl font-semibold">{t("title")}</h1>
          <p className="mt-3 max-w-xl leading-7 text-muted-foreground">
            {t("description")}
          </p>
        </section>

        <Card>
          <CardHeader>
            <CardTitle>{t("cardTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">{t("email")}</Label>
              <Input id="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <Button className="w-full" onClick={requestCode} disabled={loading}>
              {t("sendCode")}
            </Button>
            <div className="space-y-2">
              <Label htmlFor="code">{t("code")}</Label>
              <Input id="code" value={code} onChange={(event) => setCode(event.target.value)} placeholder={t("codePlaceholder")} />
            </div>
            <Button className="w-full" onClick={verifyCode} disabled={loading || code.length !== 6}>
              {t("signIn")}
            </Button>
            <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
              <Shield className="mr-2 inline h-4 w-4 text-primary" aria-hidden="true" />
              {status}
              {devCode ? <span className="ml-1 font-mono text-foreground">{t("devCode")} {devCode}</span> : null}
            </div>
            {error ? <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
          </CardContent>
        </Card>
      </main>
    </SiteShell>
  );
}
