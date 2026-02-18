// UpdateProgress — Rewrite PROGRESS.md with current state

import { Task, outputs } from "../../smithers.js";
import { makeResearcher } from "../../agents.js";
import { project } from "../../project.js";
import { renderInstructions } from "../../utils.js";
import UpdateProgressPrompt from "./prompt.mdx";

interface UpdateProgressProps {
  nodeId: string;
  /** Per-phase completion from FinalReview outputs */
  phaseStatuses: Array<{
    phaseId: string;
    phaseName: string;
    complete: boolean;
    qualityScore: number | undefined;
  }>;
  currentPass: number;
}

export function UpdateProgress({
  nodeId,
  phaseStatuses,
  currentPass,
}: UpdateProgressProps) {
  const statusSummary = phaseStatuses
    .map(
      (p) =>
        `- ${p.phaseName}: ${p.complete ? "COMPLETE" : "IN PROGRESS"}${p.qualityScore ? ` (quality: ${p.qualityScore}/10)` : ""}`,
    )
    .join("\n");

  const phaseDefinitions = project.phases
    .map((p) => `- ${p.id}: ${p.name}`)
    .join("\n");

  const projectInstructions = renderInstructions("update-progress");

  return (
    <Task
      id={nodeId}
      output={outputs.progress}
      agent={makeResearcher()} // read-only
      timeoutMs={600_000}
      retries={1}
    >
      <UpdateProgressPrompt
        currentPass={String(currentPass)}
        totalPhases={String(project.phases.length)}
        phaseStatuses={statusSummary}
        phaseDefinitions={phaseDefinitions}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
