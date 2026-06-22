import { lookup } from "node:dns/promises";

const webBaseUrl = process.env.NJUPOLY_WEB_URL ?? "https://polymarket.exnju.top";
const apiBaseUrl = process.env.NJUPOLY_API_URL ?? "https://polymarket.exnju.top/api";
const webHost = new URL(webBaseUrl).hostname;
const apiHost = new URL(apiBaseUrl).hostname;

const checks = [
  { name: "web home", url: webBaseUrl },
  { name: "web dashboard", url: `${webBaseUrl}/dashboard` },
  { name: "web forum", url: `${webBaseUrl}/forum` },
  { name: "api health", url: `${apiBaseUrl}/health`, json: true },
  { name: "api docs", url: `${apiBaseUrl}/docs` },
  { name: "api openapi", url: `${apiBaseUrl}/openapi.json`, json: true },
];

let failed = false;
const dnsFailedHosts = new Set();

for (const host of [...new Set([webHost, apiHost])]) {
  try {
    const records = await lookup(host, { all: true });
    console.log(`ok dns ${host} ${records.map((record) => record.address).join(", ")}`);
  } catch (error) {
    failed = true;
    dnsFailedHosts.add(host);
    console.error(`fail dns ${host}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

for (const check of checks) {
  const host = new URL(check.url).hostname;
  if (dnsFailedHosts.has(host)) {
    console.error(`skip ${check.name}: DNS failed for ${host}`);
    continue;
  }

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
