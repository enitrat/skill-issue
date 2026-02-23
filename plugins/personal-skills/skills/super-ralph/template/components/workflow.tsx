import { ClaudeCodeAgent, CodexAgent } from "smithers-orchestrator";
import { SuperRalph } from "super-ralph";
import { WORKFLOW_MAX_CONCURRENCY, WORKFLOW_TASK_RETRIES } from "../config";
import { outputs, smithers, Workflow } from "../smithers";
import { focuses } from "./focuses";

// TODO: Adjust URL depth so REPO_ROOT resolves to the git repository root.
//   From <repo>/workflow/components/  → use ("../..")
//   From <repo>/scripts/wf/components/ → use ("../../..")
const REPO_ROOT = new URL("{{ROOT_URL_DEPTH}}", import.meta.url).pathname.replace(
	/\/$/,
	"",
);

// ─── Agent system prompts ─────────────────────────────────────────────────────
// TODO: Replace these with project-specific instructions.
// Each prompt is injected as the systemPrompt for agents in that role.

const PLANNING_PROMPT = `You are planning work for {{PROJECT_NAME}}.

TODO: Add project-specific planning instructions here:
- Architecture rules and constraints
- Priority ordering for features
- Spec/PRD files the agent MUST read before planning
- Security invariants to maintain`;

const IMPLEMENTATION_PROMPT = `You are implementing features for {{PROJECT_NAME}}.

TODO: Add project-specific implementation instructions:
- Mandatory patterns (frameworks, error handling, etc.)
- Forbidden patterns (things to never do)
- TDD mandate: write tests FIRST
- Build/typecheck commands to run after changes`;

const TESTING_PROMPT = `You are testing {{PROJECT_NAME}}.

TODO: Add project-specific testing instructions:
- Test runner command
- Testing priorities and frameworks
- Mock/fixture patterns
- Coverage requirements`;

const REVIEWING_PROMPT = `You are reviewing code for {{PROJECT_NAME}}.

TODO: Add project-specific review instructions:
- Review checklist (same as reviewChecklist prop below)
- Severity rules: what makes an issue major vs critical
- Spec/PRD to check compliance against`;

const REPORTING_PROMPT = `Write completion reports for {{PROJECT_NAME}}.
Be concise. Report what was done, what tests pass, what remains.`;

// ─── Phase skipping ───────────────────────────────────────────────────────────

type Phase = "PROGRESS" | "CODEBASE_REVIEW" | "DISCOVER" | "TICKETS" | "INTEGRATION_TEST";
const PHASES: Phase[] = ["PROGRESS", "CODEBASE_REVIEW", "DISCOVER", "TICKETS", "INTEGRATION_TEST"];
const SKIPTO_PHASE_RAW = process.env.SKIPTO_PHASE?.trim() ?? "";
const SKIPTO_PHASE =
	SKIPTO_PHASE_RAW === ""
		? null
		: PHASES.includes(SKIPTO_PHASE_RAW as Phase)
			? (SKIPTO_PHASE_RAW as Phase)
			: null;

if (SKIPTO_PHASE_RAW !== "" && SKIPTO_PHASE == null) {
	throw new Error(
		`invalid SKIPTO_PHASE: ${SKIPTO_PHASE_RAW}. Expected one of: ${PHASES.join(", ")}`,
	);
}

// ─── Workflow ─────────────────────────────────────────────────────────────────

export default smithers((ctx) => {
	const skipPhases = new Set<string>();
	if (SKIPTO_PHASE && ctx.iteration === 0) {
		const skipIndex = PHASES.indexOf(SKIPTO_PHASE);
		PHASES.forEach((phase, i) => {
			if (i < skipIndex) skipPhases.add(phase);
		});
	}

	return (
		<Workflow name="{{PROJECT_ID}}-factory">
			<SuperRalph
				ctx={ctx}
				outputs={outputs}
				focuses={focuses}
				projectId="{{PROJECT_ID}}"
				projectName="{{PROJECT_NAME}}"
				// ── TODO: Customize these props ───────────────────────────────────
				specsPath="docs/specs/"
				referenceFiles={[
					// TODO: Paths (relative to repo root) that agents should read for context.
					// PRDs, reference implementations, existing source, etc.
					"README.md",
				]}
				buildCmds={{
					// TODO: Commands that must pass for a ticket to be "build-verified".
					typecheck: "bun run typecheck",
					build: "bun run build",
				}}
				testCmds={{
					// TODO: Commands that must pass for a ticket to be "test-verified".
					unit: "bun test",
				}}
				codeStyle={[
					// TODO: Code style rules agents must follow.
					"TypeScript, strict mode",
				].join("\n")}
				reviewChecklist={[
					// TODO: Checklist items for code/spec reviewers.
					// Agents mark severity=major/critical when these are violated.
					"Spec compliance — does implementation match the spec?",
					"Test coverage — every public API has tests",
					"Security — no injection, no leaked secrets",
				]}
				// ── Agent configuration ──────────────────────────────────────────
				maxConcurrency={WORKFLOW_MAX_CONCURRENCY}
				taskRetries={WORKFLOW_TASK_RETRIES}
				skipPhases={skipPhases}
				agents={{
					// TODO: Adjust models and timeouts per role.
					// Use agent arrays for fallback: [primary, fallback1, fallback2]
					// Available: ClaudeCodeAgent, CodexAgent, GeminiAgent, KimiAgent
					planning: new ClaudeCodeAgent({
						model: "claude-opus-4-6",
						systemPrompt: PLANNING_PROMPT,
						cwd: REPO_ROOT,
						dangerouslySkipPermissions: true,
						timeoutMs: 30 * 60 * 1000,
					}),
					implementation: new CodexAgent({
						model: "gpt-5.3-codex",
						systemPrompt: IMPLEMENTATION_PROMPT,
						config: {
							model_reasoning_effort: "high",
						},
						cwd: REPO_ROOT,
						yolo: true,
						timeoutMs: 60 * 60 * 1000,
					}),
					testing: new ClaudeCodeAgent({
						model: "claude-sonnet-4-6",
						systemPrompt: TESTING_PROMPT,
						cwd: REPO_ROOT,
						dangerouslySkipPermissions: true,
						timeoutMs: 30 * 60 * 1000,
					}),
					reviewing: new ClaudeCodeAgent({
						model: "claude-opus-4-6",
						systemPrompt: REVIEWING_PROMPT,
						cwd: REPO_ROOT,
						dangerouslySkipPermissions: true,
						timeoutMs: 20 * 60 * 1000,
					}),
					reporting: new ClaudeCodeAgent({
						model: "claude-sonnet-4-6",
						systemPrompt: REPORTING_PROMPT,
						cwd: REPO_ROOT,
						dangerouslySkipPermissions: true,
						timeoutMs: 10 * 60 * 1000,
					}),
				}}
			/>
		</Workflow>
	);
});
