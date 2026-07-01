// ReviewFix — Address issues from both reviews

import { Task, outputs } from "../../../../smithers.js";
import { makeImplementer } from "../../../../agents.js";
import { renderInstructions } from "../../../../utils.js";
import ReviewFixPrompt from "./prompt.mdx";

interface ReviewFixProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  /** Pre-formatted issue list from spec/PRD review */
  prdIssues: string;
  prdSeverity: string;
  /** Pre-formatted issue list from code review */
  codeIssues: string;
  codeSeverity: string;
  /** Whether tests are passing */
  testsPassed: boolean;
  /** Whether to skip (both reviews approved) */
  skipIf: boolean;
}

export function ReviewFix({
  nodeId,
  phaseId,
  phaseName,
  phaseMetadata,
  prdIssues,
  prdSeverity,
  codeIssues,
  codeSeverity,
  testsPassed,
  skipIf,
}: ReviewFixProps) {
  const projectInstructions = renderInstructions("review-fix", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.review_fix}
      agent={makeImplementer()}
      timeoutMs={1_800_000}
      skipIf={skipIf}
      retries={3}
    >
      <ReviewFixPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        prdIssues={prdIssues}
        prdSeverity={prdSeverity}
        codeIssues={codeIssues}
        codeSeverity={codeSeverity}
        testsPassed={String(testsPassed)}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
