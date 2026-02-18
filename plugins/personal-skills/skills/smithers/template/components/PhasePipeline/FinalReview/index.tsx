// FinalReview — readyToMoveOn gating decision

import { Task, outputs } from "../../../smithers.js";
import { makeFinalReviewer } from "../../../agents.js";
import { renderInstructions } from "../../../utils.js";
import FinalReviewPrompt from "./prompt.mdx";

interface FinalReviewProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseDescription: string;
  phaseMetadata?: Record<string, unknown>;
  pass: number;
  /** Implement output */
  whatWasDone: string;
  believesComplete: boolean;
  /** Test results */
  buildPassed: boolean;
  testsPassCount: number;
  testsFailCount: number;
  /** Review results */
  prdReviewSeverity: string;
  prdReviewApproved: boolean;
  codeReviewSeverity: string;
  codeReviewApproved: boolean;
  /** ReviewFix output */
  allIssuesResolved: boolean | undefined;
}

export function FinalReview({
  nodeId,
  phaseId,
  phaseName,
  phaseDescription,
  phaseMetadata,
  pass,
  whatWasDone,
  believesComplete,
  buildPassed,
  testsPassCount,
  testsFailCount,
  prdReviewSeverity,
  prdReviewApproved,
  codeReviewSeverity,
  codeReviewApproved,
  allIssuesResolved,
}: FinalReviewProps) {
  const projectInstructions = renderInstructions("final-review", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.final_review}
      agent={makeFinalReviewer()}
      timeoutMs={600_000}
      retries={1}
    >
      <FinalReviewPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        phaseDescription={phaseDescription}
        pass={String(pass)}
        whatWasDone={whatWasDone}
        believesComplete={String(believesComplete)}
        buildPassed={String(buildPassed)}
        testsPassCount={String(testsPassCount)}
        testsFailCount={String(testsFailCount)}
        prdReviewSeverity={prdReviewSeverity}
        prdReviewApproved={String(prdReviewApproved)}
        codeReviewSeverity={codeReviewSeverity}
        codeReviewApproved={String(codeReviewApproved)}
        allIssuesResolved={String(allIssuesResolved ?? "N/A")}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
