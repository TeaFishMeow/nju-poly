const DEFAULT_API_BASE_URL = process.env.NODE_ENV === "production" ? "https://polymarket.exnju.top/api" : "http://127.0.0.1:8000";
const API_TIMEOUT_MS = 15_000;

function normalizeApiBaseUrl(value: string | undefined): string {
  const cleaned = (value ?? DEFAULT_API_BASE_URL).replace(/^[\uFEFF\u200B-\u200D\u2060]+/, "").trim().replace(/\/+$/, "");
  if (cleaned.startsWith("http://") || cleaned.startsWith("https://") || cleaned.startsWith("/")) {
    return cleaned;
  }
  return DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = normalizeApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId: ReturnType<typeof setTimeout> = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  const abortFromCaller = () => controller.abort();
  init?.signal?.addEventListener("abort", abortFromCaller, { once: true });

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    init?.signal?.removeEventListener("abort", abortFromCaller);
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof detail.detail === "string" ? detail.detail : response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}
