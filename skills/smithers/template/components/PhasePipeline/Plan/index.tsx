// Plan — Create implementation plan from research findings

import { Task, outputs } from "../../../smithers.js";
import { makeResearcher } from "../../../agents.js";
import { renderInstructions } from "../../../utils.js";
import PlanPrompt from "./prompt.mdx";

interface PlanProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseDescription: string;
  phaseMetadata?: Record<string, unknown>;
  contextFilePath: string;
  /** Pre-formatted findings string (e.g. "- finding1\n- finding2") */
  findings: string;
  planOutputPath: string;
}

export function Plan({
  nodeId,
  phaseId,
  phaseName,
  phaseDescription,
  phaseMetadata,
  contextFilePath,
  findings,
  planOutputPath,
}: PlanProps) {
  const projectInstructions = renderInstructions("plan", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.plan}
      agent={makeResearcher()} // planner uses read-only agent
      timeoutMs={3_600_000}
      retries={3}
    >
      <PlanPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        phaseDescription={phaseDescription}
        contextFilePath={contextFilePath}
        findings={findings}
        planOutputPath={planOutputPath}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
