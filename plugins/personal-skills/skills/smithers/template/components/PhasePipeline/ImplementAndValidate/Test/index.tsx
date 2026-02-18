// Test — Run build + tests, report results

import { Task, outputs } from "../../../../smithers.js";
import { makeImplementer } from "../../../../agents.js";
import { renderInstructions } from "../../../../utils.js";
import TestPrompt from "./prompt.mdx";

interface TestProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  /** Pre-formatted lists of files created/modified by Implement step */
  filesCreated: string;
  filesModified: string;
  /** What was done in implementation */
  whatWasDone: string;
}

export function Test({
  nodeId,
  phaseId,
  phaseName,
  phaseMetadata,
  filesCreated,
  filesModified,
  whatWasDone,
}: TestProps) {
  const projectInstructions = renderInstructions("test", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.test_results}
      agent={makeImplementer()} // needs write access to fix compilation errors
      timeoutMs={600_000}
      retries={2}
    >
      <TestPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={whatWasDone}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
