// Implement — Execute implementation with feedback loop

import { Task, outputs } from "../../../../smithers.js";
import { makeImplementer } from "../../../../agents.js";
import { renderInstructions } from "../../../../utils.js";
import ImplementPrompt from "./prompt.mdx";

interface ImplementProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  planFilePath: string;
  contextFilePath: string;
  /** Pre-formatted numbered implementation steps */
  implementationSteps: string;
  /** Previous iteration's summary (for iterative refinement) */
  previousSummary: string | undefined;
  previousNextSteps: string | undefined;
  /** Review feedback from previous iteration */
  prdReviewFeedback: string | undefined;
  codeReviewFeedback: string | undefined;
  /** Failing tests from previous iteration */
  failingTests: string | undefined;
  /** Final review reasoning from previous iteration */
  finalReviewFeedback: string | undefined;
  /** Review fix summary from previous iteration */
  reviewFixSummary: string | undefined;
  /** Current pass number */
  pass: number;
}

export function Implement({
  nodeId,
  phaseId,
  phaseName,
  phaseMetadata,
  planFilePath,
  contextFilePath,
  implementationSteps,
  previousSummary,
  previousNextSteps,
  prdReviewFeedback,
  codeReviewFeedback,
  failingTests,
  finalReviewFeedback,
  reviewFixSummary,
  pass,
}: ImplementProps) {
  const projectInstructions = renderInstructions("implement", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.implement}
      agent={makeImplementer()}
      timeoutMs={3_600_000}
      retries={5}
    >
      <ImplementPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        planFilePath={planFilePath}
        contextFilePath={contextFilePath}
        implementationSteps={implementationSteps}
        previousSummary={previousSummary ?? ""}
        previousNextSteps={previousNextSteps ?? ""}
        prdReviewFeedback={prdReviewFeedback ?? ""}
        codeReviewFeedback={codeReviewFeedback ?? ""}
        failingTests={failingTests ?? ""}
        finalReviewFeedback={finalReviewFeedback ?? ""}
        reviewFixSummary={reviewFixSummary ?? ""}
        pass={String(pass)}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
