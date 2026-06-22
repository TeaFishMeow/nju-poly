import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const arg = process.argv[i];
  if (!arg.startsWith("--")) {
    continue;
  }
  const next = process.argv[i + 1];
  if (next && !next.startsWith("--")) {
    args.set(arg, next);
    i += 1;
  } else {
    args.set(arg, true);
  }
}

const targetPath = resolve(args.get("--target") ?? "apps/api/.env");
const key = args.get("--key");
let value = args.get("--value");

if (!key || !/^[A-Z][A-Z0-9_]*$/.test(key)) {
  throw new Error("usage: node deploy/set-production-env.mjs --key KEY [--value VALUE|--stdin]");
}

if (args.has("--stdin")) {
  value = readFileSync(0, "utf8").replace(/\r?\n$/, "");
}

if (typeof value !== "string" || value.length === 0) {
  throw new Error(`missing value for ${key}`);
}

function readEnv(path) {
  const lines = existsSync(path) ? readFileSync(path, "utf8").split(/\r?\n/) : [];
  const entries = [];
  const seen = new Set();

  for (const line of lines) {
    if (/^[A-Za-z_][A-Za-z0-9_]*=/.test(line)) {
      const index = line.indexOf("=");
      const name = line.slice(0, index);
      entries.push({ kind: "entry", key: name, value: line.slice(index + 1) });
      seen.add(name);
    } else if (line.length > 0) {
      entries.push({ kind: "raw", value: line });
    }
  }

  return { entries, seen };
}

const { entries, seen } = readEnv(targetPath);
let updated = false;

for (const entry of entries) {
  if (entry.kind === "entry" && entry.key === key) {
    entry.value = value;
    updated = true;
  }
}

if (!seen.has(key)) {
  entries.push({ kind: "entry", key, value });
  updated = true;
}

if (!updated) {
  throw new Error(`failed to update ${key}`);
}

const output = entries
  .map((entry) => (entry.kind === "entry" ? `${entry.key}=${entry.value}` : entry.value))
  .join("\n");

writeFileSync(targetPath, `${output}\n`, { mode: 0o600 });
console.log(`updated ${key}`);
