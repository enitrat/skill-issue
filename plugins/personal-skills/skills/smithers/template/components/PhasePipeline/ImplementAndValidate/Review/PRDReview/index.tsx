// PRDReview — Verify implementation matches spec/PRD

import { Task, outputs } from "../../../../../smithers.js";
import { makePRDReviewer } from "../../../../../agents.js";
import { renderInstructions } from "../../../../../utils.js";
import PRDReviewPrompt from "./prompt.mdx";

interface PRDReviewProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  filesCreated: string;
  filesModified: string;
  whatWasDone: string;
  buildPassed: boolean;
  testsPassCount: number;
  testsFailCount: number;
  failingSummary: string | null;
}

export function PRDReview({
  nodeId,
  phaseId,
  phaseName,
  phaseMetadata,
  filesCreated,
  filesModified,
  whatWasDone,
  buildPassed,
  testsPassCount,
  testsFailCount,
  failingSummary,
}: PRDReviewProps) {
  const projectInstructions = renderInstructions("prd-review", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.prd_review}
      agent={makePRDReviewer()}
      timeoutMs={600_000}
      continueOnFail
      retries={1}
    >
      <PRDReviewPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={whatWasDone}
        buildPassed={String(buildPassed)}
        testsPassCount={String(testsPassCount)}
        testsFailCount={String(testsFailCount)}
        failingSummary={failingSummary ?? "none"}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
