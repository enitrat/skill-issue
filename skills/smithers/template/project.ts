// project.ts — Load project configuration from env var or default
//
// Usage:
//   SMITHERS_PROJECT=./smithers-config.js bunx smithers run workflow.tsx
//   (or set SMITHERS_PROJECT env var to point to your config file)

import type { ProjectConfig } from "./types/project.js";

const configPath =
  process.env.SMITHERS_PROJECT ??
  "./smithers-config.js";

const mod = await import(configPath);
export const project: ProjectConfig = mod.default;
