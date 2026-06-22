const webBaseUrl = process.env.NJUPOLY_WEB_URL ?? "https://polymarket.exnju.top";
const apiBaseUrl = process.env.NJUPOLY_API_URL ?? "https://api.polymarket.exnju.top";

const checks = [
  { name: "web home", url: webBaseUrl },
  { name: "web dashboard", url: `${webBaseUrl}/dashboard` },
  { name: "web forum", url: `${webBaseUrl}/forum` },
  { name: "api health", url: `${apiBaseUrl}/health`, json: true },
  { name: "api docs", url: `${apiBaseUrl}/docs` },
  { name: "api openapi", url: `${apiBaseUrl}/openapi.json`, json: true },
];

let failed = false;

for (const check of checks) {
  try {
    const response = await fetch(check.url, { redirect: "follow" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    if (check.json) {
      await response.json();
    }
    console.log(`ok ${check.name} ${response.status}`);
  } catch (error) {
    failed = true;
    console.error(`fail ${check.name}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

if (failed) {
  process.exit(1);
}
