// index.ts — Public re-exports for project config files
//
// Project configs (smithers-config/config.ts) import agent classes from here
// so they resolve against the engine's node_modules, not the config directory.
//
// Usage in config.ts:
//   import { ClaudeCodeAgent, CodexAgent } from "../../engine/index.js";

export { ClaudeCodeAgent, CodexAgent } from "smithers-orchestrator";
export type { ProjectConfig, BaseCliAgent, AgentRole, Phase } from "./types/project.js";
