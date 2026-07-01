// Research — Gather reference material before implementation

import { Task, outputs } from "../../../smithers.js";
import { makeResearcher } from "../../../agents.js";
import { renderInstructions } from "../../../utils.js";
import ResearchPrompt from "./prompt.mdx";

interface ResearchProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseDescription: string;
  phaseMetadata?: Record<string, unknown>;
  outputPath: string;
}

export function Research({
  nodeId,
  phaseId,
  phaseName,
  phaseDescription,
  phaseMetadata,
  outputPath,
}: ResearchProps) {
  const projectInstructions = renderInstructions("research", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.research}
      agent={makeResearcher()}
      timeoutMs={3_600_000}
      retries={3}
    >
      <ResearchPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        phaseDescription={phaseDescription}
        outputPath={outputPath}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
