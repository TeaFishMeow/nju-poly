import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

mkdirSync(resolve(process.cwd(), ".local"), { recursive: true });
