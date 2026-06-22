"use client";

import Link from "next/link";
import { LayoutDashboard } from "lucide-react";
import { useTranslations } from "next-intl";

import { BrandLockup } from "@/components/brand-logo";
import { LocaleToggle } from "@/components/locale-toggle";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/", labelKey: "home" },
  { href: "/gacha", labelKey: "gacha" },
  { href: "/forum", labelKey: "forum" },
] as const;

export function SiteShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations("shell");

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b bg-background/92 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 sm:gap-4 sm:px-6">
          <Link href="/" className="min-w-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <BrandLockup />
          </Link>

          <nav className="ml-auto hidden items-center gap-1 md:flex">
            {navItems.map((item) => (
              <Button key={item.href} asChild variant="ghost" size="sm">
                <Link href={item.href}>{t(item.labelKey)}</Link>
              </Button>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2 md:ml-2">
            <ThemeToggle />
            <LocaleToggle className="hidden sm:inline-flex" />
            <Button asChild size="sm" aria-label={t("openDashboard")} className="hidden sm:inline-flex">
              <Link href="/dashboard">
                <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">{t("dashboard")}</span>
              </Link>
            </Button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-7xl gap-2 overflow-x-auto border-t px-4 py-2 sm:px-6 md:hidden">
          {navItems.map((item) => (
            <Button key={item.href} asChild variant="ghost" size="sm" className="shrink-0">
              <Link href={item.href}>{t(item.labelKey)}</Link>
            </Button>
          ))}
          <Button asChild variant="ghost" size="sm" className="shrink-0">
            <Link href="/login">{t("login")}</Link>
          </Button>
          <Button asChild variant="ghost" size="sm" className="shrink-0 sm:hidden">
            <Link href="/dashboard">{t("dashboard")}</Link>
          </Button>
          <LocaleToggle className="shrink-0 sm:hidden" />
        </nav>
      </header>
      {children}
    </div>
  );
}
