import { cookies } from "next/headers";

import { createTranslator, defaultLocale, isLocale, localeCookieName, messages } from "@/i18n/messages";

export async function getCurrentLocale() {
  const cookieStore = await cookies();
  const requestedLocale = cookieStore.get(localeCookieName)?.value;

  return isLocale(requestedLocale) ? requestedLocale : defaultLocale;
}

export async function getDictionary() {
  const locale = await getCurrentLocale();
  const dictionary = messages[locale];

  return {
    dictionary,
    locale,
    t: createTranslator(dictionary),
  };
}
