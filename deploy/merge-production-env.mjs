import { randomBytes } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const targetPath = resolve(args.get("--target") ?? "apps/api/.env");
const apiEnvPath = args.get("--api-env");
const rootEnvPath = args.get("--root-env");

function readEnv(path) {
  const values = {};
  if (!path || !existsSync(path)) {
    return values;
  }

  for (const line of readFileSync(path, "utf8").split(/\r?\n/)) {
    if (!/^[A-Za-z_][A-Za-z0-9_]*=/.test(line)) {
      continue;
    }
    const index = line.indexOf("=");
    values[line.slice(0, index)] = line.slice(index + 1);
  }

  return values;
}

const data = readEnv(targetPath);
const apiEnv = readEnv(apiEnvPath);
const rootEnv = readEnv(rootEnvPath);

const copiedKeys = [];
for (const key of [
  "SMTP_HOST",
  "SMTP_PORT",
  "SMTP_USERNAME",
  "SMTP_PASSWORD",
  "SMTP_FROM",
  "SMTP_USE_TLS",
  "SMTP_USE_SSL",
]) {
  if (apiEnv[key]) {
    data[key] = apiEnv[key];
    copiedKeys.push(key);
  }
}

if (rootEnv.IMAGE_MODEL_API_KEY) {
  data.IMAGE_MODEL_API_KEY = rootEnv.IMAGE_MODEL_API_KEY;
  copiedKeys.push("IMAGE_MODEL_API_KEY");
}

if (!data.SESSION_TOKEN_SECRET || data.SESSION_TOKEN_SECRET.startsWith("REPLACE_")) {
  data.SESSION_TOKEN_SECRET = randomBytes(32).toString("hex");
  copiedKeys.push("SESSION_TOKEN_SECRET");
}

const order = [
  "DATABASE_URL",
  "CORS_ORIGINS",
  "ADMIN_STUDENT_IDS",
  "SESSION_TOKEN_SECRET",
  "SESSION_TOKEN_TTL_DAYS",
  "VERIFICATION_CODE_TTL_MINUTES",
  "SMTP_HOST",
  "SMTP_PORT",
  "SMTP_USERNAME",
  "SMTP_PASSWORD",
  "SMTP_FROM",
  "SMTP_USE_TLS",
  "SMTP_USE_SSL",
  "IMAGE_MODEL_BASE_URL",
  "IMAGE_MODEL_NAME",
  "IMAGE_MODEL_API_KEY",
  "MEDIA_STORAGE_DIR",
  "MEDIA_PUBLIC_BASE_URL",
];

writeFileSync(
  targetPath,
  `${order.map((key) => `${key}=${data[key] ?? ""}`).join("\n")}\n`,
  { mode: 0o600 },
);

console.log(`updated production env keys: ${copiedKeys.sort().join(", ")}`);
