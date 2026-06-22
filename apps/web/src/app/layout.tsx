import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { ThemeProvider } from "@/components/theme-provider";
import { getCurrentLocale } from "@/i18n/server";
import { messages } from "@/i18n/messages";
import "./globals.css";

export const metadata: Metadata = {
  title: "南哪竞猜 NJUPoly",
  description: "Campus prediction market prototype",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getCurrentLocale();

  return (
    <html lang={locale === "zh" ? "zh-CN" : "en"} suppressHydrationWarning>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages[locale]}>
          <ThemeProvider>{children}</ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
