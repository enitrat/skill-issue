#!/usr/bin/env bun

/**
 * {{PROJECT_NAME}} — super-ralph run manager
 *
 * Usage:
 *   bun run index.ts                              — interactive run picker
 *   SKIPTO_PHASE=TICKETS bun run index.ts         — skip to ticket work
 *   WORKFLOW_MAX_CONCURRENCY=4 bun run index.ts   — tune concurrency
 *
 * Phases: PROGRESS → CODEBASE_REVIEW → DISCOVER → TICKETS → INTEGRATION_TEST
 */

import { existsSync } from "node:fs";
import { createInterface } from "node:readline";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Database } from "bun:sqlite";
import { $ } from "bun";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// TODO: Adjust depth to match your repo layout.
// If workflow dir is at <repo>/scripts/workflow/, use ("../..")
// If workflow dir is at <repo>/workflow/, use ("..")
const ROOT_DIR = resolve(__dirname, "{{ROOT_RELATIVE}}");
const DB_PATH = join(__dirname, "{{PROJECT_ID}}-build.db");
const WORKFLOW = "components/workflow.tsx";

const maxConcurrency = parseInt(
	process.env.WORKFLOW_MAX_CONCURRENCY || "8",
	10,
);

// ─── ANSI helpers ─────────────────────────────────────────────────────────────

const c = {
	reset: "\x1b[0m",
	bold: "\x1b[1m",
	dim: "\x1b[2m",
	green: "\x1b[32m",
	yellow: "\x1b[33m",
	red: "\x1b[31m",
	cyan: "\x1b[36m",
	gray: "\x1b[90m",
};

const bold = (s: string) => `${c.bold}${s}${c.reset}`;
const dim = (s: string) => `${c.dim}${s}${c.reset}`;
const green = (s: string) => `${c.green}${s}${c.reset}`;
const yellow = (s: string) => `${c.yellow}${s}${c.reset}`;
const red = (s: string) => `${c.red}${s}${c.reset}`;
const cyan = (s: string) => `${c.cyan}${s}${c.reset}`;

function colorStatus(status: string): string {
	switch (status) {
		case "running":
		case "waiting-approval":
			return yellow(status);
		case "done":
		case "completed":
			return green(status);
		case "cancelled":
			return dim(status);
		case "failed":
		case "error":
			return red(status);
		default:
			return dim(status);
	}
}

function relativeTime(ms: number | null): string {
	if (!ms) return dim("—");
	const diff = Date.now() - ms;
	const mins = Math.floor(diff / 60_000);
	if (mins < 1) return "just now";
	if (mins < 60) return `${mins}m ago`;
	const hrs = Math.floor(mins / 60);
	if (hrs < 24) return `${hrs}h ago`;
	return `${Math.floor(hrs / 24)}d ago`;
}

// ─── DB queries ───────────────────────────────────────────────────────────────

type RunRow = {
	run_id: string;
	workflow_name: string;
	status: string;
	created_at_ms: number | null;
	started_at_ms: number | null;
	finished_at_ms: number | null;
};

function listRuns(): RunRow[] {
	if (!existsSync(DB_PATH)) return [];
	try {
		const db = new Database(DB_PATH, { readonly: true });
		const rows = db
			.query<RunRow, []>(
				`SELECT run_id, workflow_name, status, created_at_ms, started_at_ms, finished_at_ms
         FROM _smithers_runs ORDER BY created_at_ms DESC LIMIT 50`,
			)
			.all();
		db.close();
		return rows;
	} catch {
		return [];
	}
}

function deleteRun(runId: string): void {
	const db = new Database(DB_PATH);
	for (const table of [
		"_smithers_runs",
		"_smithers_nodes",
		"_smithers_attempts",
		"_smithers_frames",
		"_smithers_approvals",
		"_smithers_tool_calls",
		"_smithers_events",
	]) {
		try {
			db.run(`DELETE FROM ${table} WHERE run_id = ?`, [runId]);
		} catch {
			/* table may not exist yet */
		}
	}
	db.close();
}

// ─── Readline ─────────────────────────────────────────────────────────────────

function ask(prompt: string): Promise<string> {
	const rl = createInterface({ input: process.stdin, output: process.stdout, terminal: true });
	return new Promise((resolve) => {
		rl.question(prompt, (answer) => {
			rl.close();
			resolve(answer.trim());
		});
	});
}

// ─── Smithers CLI ─────────────────────────────────────────────────────────────

function findSmithersCli(): string | null {
	const local = join(__dirname, "node_modules/smithers-orchestrator/src/cli/index.ts");
	if (existsSync(local)) return local;
	const home = join(process.env.HOME || "", "smithers/src/cli/index.ts");
	if (existsSync(home)) return home;
	return null;
}

function setupEnv() {
	process.env.USE_CLI_AGENTS = "1";
	delete process.env.CLAUDECODE;
	process.env.SMITHERS_DEBUG = "1";
}

async function runNew(cli: string) {
	console.log(`\n${bold("Starting new run")}`);
	console.log(dim(`root: ${ROOT_DIR}  concurrency: ${maxConcurrency}\n`));
	await $`bun run ${cli} run ${WORKFLOW} --root ${ROOT_DIR} --max-concurrency ${maxConcurrency}`.cwd(__dirname);
}

async function runResume(cli: string, runId: string) {
	console.log(`\n${bold("Resuming")} ${cyan(runId)}\n`);
	await $`bun run ${cli} resume ${WORKFLOW} --run-id ${runId} --root ${ROOT_DIR} --max-concurrency ${maxConcurrency}`.cwd(__dirname);
}

async function runCancel(cli: string, runId: string) {
	console.log(`\n${yellow("Cancelling")} ${cyan(runId)}…`);
	await $`bun run ${cli} cancel ${WORKFLOW} --run-id ${runId}`.cwd(__dirname);
	console.log(green("Cancelled."));
}

// ─── Display ──────────────────────────────────────────────────────────────────

const TITLE = "{{PROJECT_NAME}}";

function printHeader() {
	console.clear();
	console.log(`\n${bold(cyan(`  ${TITLE}`))}  ${dim("— run manager")}\n`);
}

function printRunTable(runs: RunRow[]) {
	const SEP = dim("  " + "─".repeat(72));
	console.log(SEP);
	for (const [i, run] of runs.entries()) {
		const idx = bold(String(i + 1).padStart(2));
		const status = colorStatus(run.status).padEnd(20);
		const id = cyan(run.run_id.slice(0, 20).padEnd(22));
		const time = dim(relativeTime(run.started_at_ms ?? run.created_at_ms).padEnd(12));
		const fin = run.finished_at_ms ? dim(`  finished ${relativeTime(run.finished_at_ms)}`) : "";
		console.log(`  ${idx}  ${status}  ${id}  ${time}${fin}`);
	}
	console.log(SEP);
}

// ─── Menus ────────────────────────────────────────────────────────────────────

async function runMenu(runs: RunRow[], cli: string): Promise<void> {
	printHeader();
	if (runs.length === 0) {
		console.log(dim("  No previous runs found.\n"));
		console.log(`  ${bold("n")}  Start a new run`);
		console.log(`  ${bold("q")}  Quit\n`);
		const ans = await ask("  Select [n/q]: ");
		if (ans === "n") return runNew(cli);
		process.exit(0);
	}
	console.log(`  ${bold("Existing runs:")}\n`);
	printRunTable(runs);
	console.log(`\n  ${bold("n")}  Start a new run    ${bold("q")}  Quit\n`);
	const ans = await ask(`  Select a run [1–${runs.length} / n / q]: `);
	if (ans === "q") process.exit(0);
	if (ans === "n") return runNew(cli);
	const idx = parseInt(ans, 10);
	if (Number.isNaN(idx) || idx < 1 || idx > runs.length) {
		console.log(red("\n  Invalid selection.\n"));
		await Bun.sleep(800);
		return runMenu(runs, cli);
	}
	return actionMenu(runs[idx - 1]!, cli);
}

async function actionMenu(run: RunRow, cli: string): Promise<void> {
	printHeader();
	console.log(`  Run   ${cyan(run.run_id)}`);
	console.log(`  Status  ${colorStatus(run.status)}    ${dim(relativeTime(run.started_at_ms ?? run.created_at_ms))}\n`);
	const isActive = run.status === "running" || run.status === "waiting-approval";
	const opts: Array<{ key: string; label: string }> = [];
	opts.push({ key: "r", label: "Resume this run" });
	if (isActive) opts.push({ key: "c", label: "Cancel this run" });
	opts.push({ key: "d", label: red("Delete this run") });
	opts.push({ key: "b", label: "Back" });
	for (const o of opts) console.log(`  ${bold(o.key)}  ${o.label}`);
	const ans = await ask(`\n  Action [${opts.map((o) => o.key).join("/")}]: `);
	if (ans === "b") return runMenu(listRuns(), cli);
	if (ans === "r") return runResume(cli, run.run_id);
	if (ans === "c" && isActive) {
		if ((await ask(`  ${yellow("Cancel")} ${cyan(run.run_id)}? [y/N]: `)).toLowerCase() === "y") {
			await runCancel(cli, run.run_id);
			await Bun.sleep(600);
			return runMenu(listRuns(), cli);
		}
		return actionMenu(run, cli);
	}
	if (ans === "d") {
		if ((await ask(`  ${red("Permanently delete")} ${cyan(run.run_id)}? [y/N]: `)).toLowerCase() === "y") {
			deleteRun(run.run_id);
			console.log(green(`\n  Deleted ${run.run_id}.`));
			await Bun.sleep(600);
			return runMenu(listRuns(), cli);
		}
		return actionMenu(run, cli);
	}
	console.log(red("\n  Invalid selection.\n"));
	await Bun.sleep(500);
	return actionMenu(run, cli);
}

// ─── Entry point ──────────────────────────────────────────────────────────────

const smithersCli = findSmithersCli();
if (!smithersCli) {
	console.error("error: smithers CLI not found in node_modules or ~/smithers");
	process.exit(1);
}
setupEnv();
await runMenu(listRuns(), smithersCli);
