// workflow.tsx — Root workflow composition
//
// Outer Ralph loop iterates over all phases from the project config.
// Phases that complete (readyToMoveOn: true) are skipped on subsequent passes.
// Pass tracker records which pass just completed.
// Caching enabled for crash recovery and re-run optimization.

import {
  Workflow,
  Ralph,
  Sequence,
  Task,
  outputs,
  smithers,
  useCtx,
} from "./smithers.js";
import { project } from "./project.js";
import PhasePipeline from "./components/PhasePipeline/index.js";
import { UpdateProgress } from "./components/UpdateProgress/index.js";

const SKIP_PHASES = new Set(
  (process.env.SKIP_PHASES ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
);

export default smithers((ctx) => {
  // ─────────────────────────────────────────────────────────
  // Phase completion gating
  // ─────────────────────────────────────────────────────────

  const phaseComplete = (id: string): boolean => {
    const finalReview = ctx.latest("final_review", `${id}:final-review`);
    return finalReview?.readyToMoveOn ?? false;
  };

  const phaseQualityScore = (id: string): number | undefined => {
    const finalReview = ctx.latest("final_review", `${id}:final-review`);
    return finalReview?.qualityScore;
  };

  // ─────────────────────────────────────────────────────────
  // Pass tracking
  // ─────────────────────────────────────────────────────────

  const passTracker = ctx.latest("pass_tracker", "pass-tracker");
  const currentPass = passTracker?.totalIterations ?? 0;

  const { phases, maxPasses } = project;
  const activePhases = phases.filter(({ id }) => !SKIP_PHASES.has(id));

  // ─────────────────────────────────────────────────────────
  // Termination conditions
  // ─────────────────────────────────────────────────────────

  const allPhasesComplete = activePhases.every(({ id }) => phaseComplete(id));
  const done = currentPass >= maxPasses || allPhasesComplete;

  // ─────────────────────────────────────────────────────────
  // Phase statuses for UpdateProgress
  // ─────────────────────────────────────────────────────────

  const phaseStatuses = phases.map(({ id, name }) => ({
    phaseId: id,
    phaseName: name,
    complete: phaseComplete(id),
    qualityScore: phaseQualityScore(id),
  }));

  // ─────────────────────────────────────────────────────────
  // Workflow tree
  // ─────────────────────────────────────────────────────────

  return (
    <Workflow name={project.workflowName} cache>
      <Ralph
        until={done}
        maxIterations={maxPasses * phases.length * 20}
        onMaxReached="return-last"
      >
        <Sequence>
          {/* 0. Update progress at the start of each pass */}
          <UpdateProgress
            nodeId="update-progress"
            phaseStatuses={phaseStatuses}
            currentPass={currentPass}
          />

          {/* 1-N. Process each phase (skip completed + env-skipped) */}
          {phases.map(({ id, name, description, metadata }) => (
            <PhasePipeline
              key={id}
              phaseId={id}
              phaseName={name}
              phaseDescription={description}
              phaseMetadata={metadata}
              pass={currentPass + 1}
              skipIf={phaseComplete(id) || SKIP_PHASES.has(id)}
            />
          ))}

          {/* Pass tracker — records which pass just completed */}
          <Task
            id="pass-tracker"
            output={outputs.pass_tracker}
          >
            {{
              totalIterations: currentPass + 1,
              phasesRun: phases
                .filter(({ id }) => !SKIP_PHASES.has(id) && !phaseComplete(id))
                .map(({ id }) => id),
              phasesComplete: phases
                .filter(({ id }) => phaseComplete(id))
                .map(({ id }) => id),
              summary: `Pass ${currentPass + 1} of ${maxPasses} complete. ${
                activePhases.filter(({ id }) => phaseComplete(id)).length
              }/${activePhases.length} phases done.`,
            }}
          </Task>
        </Sequence>
      </Ralph>
    </Workflow>
  );
});
