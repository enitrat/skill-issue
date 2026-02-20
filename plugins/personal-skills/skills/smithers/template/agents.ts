// agents.ts — Generic agent factory with per-role specs from project config
//
// Each make*() function returns the override agent directly if provided, otherwise
// constructs a hardcoded default. No shared ROLE_DEFAULTS table — each factory
// is self-contained and independently readable.

import { ClaudeCodeAgent, CodexAgent } from "smithers-orchestrator";
// Also available: GeminiAgent, KimiAgent, PiAgent — import directly from "smithers-orchestrator"
// and provide as agent overrides in your project config.
import { project } from "./project.js";

// ─────────────────────────────────────────────────────────────
// Generic system prompt sections (project-agnostic)
// ─────────────────────────────────────────────────────────────

const WORKSPACE_POLICY = `
## WORKSPACE POLICY

Uncommitted changes in the worktree are expected and normal.
Do NOT refuse to work because of dirty git state. Proceed with implementation regardless.
Other agents in this workflow may have made changes that are not yet committed.
`;

const JSON_OUTPUT = `
## CRITICAL: Output Rules

1. ALWAYS wait for ALL tasks and sub-agents to fully complete before producing
   any final output. Never respond while work is still in progress.
2. Your FINAL message MUST end with a JSON object wrapped in a code fence.
   The JSON format is specified in your task prompt. No text after the JSON.
3. Never reference "earlier responses" — your output is captured from a
   single response. All content must be in that one response.
4. Background tasks: if you used run_in_background: true on ANY tool call, you
   MUST call TaskOutput (with block: true) to retrieve every background task's
   result before writing your final JSON. Your output is captured the moment you
   respond — background tasks that are still running when you write the JSON are
   silently discarded. Do not produce the final JSON until you have explicitly
   read ALL background task outputs via TaskOutput.
`;

// ─────────────────────────────────────────────────────────────
// System prompt builder
// ─────────────────────────────────────────────────────────────

function buildSystemPrompt(description: string): string {
  return [
    `# Role: ${description}`,
    project.agents.systemPromptContent,
    WORKSPACE_POLICY,
    JSON_OUTPUT,
  ]
    .filter(Boolean)
    .join("\n\n");
}

// ─────────────────────────────────────────────────────────────
// Agent factories
//
// Pattern: return the override agent if provided, else construct a default.
// Overrides are full ClaudeCodeAgent | CodexAgent instances — the caller
// controls every parameter (model, systemPrompt, cwd, timeoutMs, etc.).
// ─────────────────────────────────────────────────────────────

export function makeImplementer(): CodexAgent | ClaudeCodeAgent {
  const o = project.agents.overrides?.implementer;
  if (o) return o;
  return new CodexAgent({
    model: "gpt-5.3-codex",
    systemPrompt: buildSystemPrompt("Implementer — Write code and make changes"),
    yolo: true,
    cwd: project.cwd,
    timeoutMs: 3_600_000,
  });
}

export function makeResearcher(): ClaudeCodeAgent | CodexAgent {
  const o = project.agents.overrides?.researcher;
  if (o) return o;
  return new ClaudeCodeAgent({
    model: "claude-opus-4-6",
    systemPrompt: buildSystemPrompt(
      "Researcher — Gather reference material from existing codebases",
    ),
    permissionMode: "default",
    cwd: project.cwd,
    timeoutMs: 1_800_000,
  });
}

export function makePRDReviewer(): ClaudeCodeAgent | CodexAgent {
  const o = project.agents.overrides?.prdReviewer;
  if (o) return o;
  return new ClaudeCodeAgent({
    model: "claude-opus-4-6",
    systemPrompt: buildSystemPrompt(
      "Spec Reviewer — Verify implementation matches specification",
    ),
    permissionMode: "default",
    cwd: project.cwd,
    timeoutMs: 1_800_000,
  });
}

export function makeCodeReviewer(): ClaudeCodeAgent | CodexAgent {
  const o = project.agents.overrides?.codeReviewer;
  if (o) return o;
  return new ClaudeCodeAgent({
    model: "claude-opus-4-6",
    systemPrompt: buildSystemPrompt(
      "Code Reviewer — Check code quality, conventions, test coverage, security",
    ),
    permissionMode: "default",
    cwd: project.cwd,
    timeoutMs: 1_800_000,
  });
}

export function makeFinalReviewer(): ClaudeCodeAgent | CodexAgent {
  const o = project.agents.overrides?.finalReviewer;
  if (o) return o;
  return new ClaudeCodeAgent({
    model: "claude-opus-4-6",
    systemPrompt: buildSystemPrompt(
      "Final Reviewer — Decide if a phase is complete and ready to move on",
    ),
    permissionMode: "default",
    cwd: project.cwd,
    timeoutMs: 1_800_000,
  });
}
