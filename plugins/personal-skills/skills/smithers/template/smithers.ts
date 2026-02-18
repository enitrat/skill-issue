// smithers.ts — Smithers orchestrator setup with schema registry and caching
//
// This is the framework entry point. It creates:
// - SQLite database for state persistence (named after the project)
// - Auto-generated tables from Zod schemas
// - JSX primitives (Workflow, Task from createSmithers; Sequence, Parallel, Ralph, Branch direct)
// - ctx.outputMaybe() for reading cached outputs
// - Caching enabled for crash recovery and re-run optimization

import {
  createSmithers,
  Sequence,
  Parallel,
  Ralph,
  Branch,
} from "smithers-orchestrator";
import { outputSchemas } from "./components/schemas.js";
import { project } from "./project.js";

const DB_PATH = `./${project.workflowName}.db`;

const api = createSmithers(outputSchemas, {
  dbPath: DB_PATH,
});

export const { Workflow, Task, useCtx, smithers, outputs, db } = api;

// Re-export JSX primitives for components to import from one place
export { Sequence, Parallel, Ralph, Branch };
