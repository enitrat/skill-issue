// Review — Parallel wrapper for CodeReview + PRDReview

import { Parallel } from "../../../../smithers.js";
import { PRDReview } from "./PRDReview/index.js";
import { CodeReview } from "./CodeReview/index.js";

interface ReviewProps {
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  filesCreated: string;
  filesModified: string;
  whatWasDone: string;
  buildPassed: boolean;
  testsPassed: boolean;
  testsPassCount: number;
  testsFailCount: number;
  failingSummary: string | null;
}

export function Review({
  phaseId,
  phaseName,
  phaseMetadata,
  filesCreated,
  filesModified,
  whatWasDone,
  buildPassed,
  testsPassed,
  testsPassCount,
  testsFailCount,
  failingSummary,
}: ReviewProps) {
  return (
    <Parallel>
      <PRDReview
        nodeId={`${phaseId}:prd-review`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={whatWasDone}
        buildPassed={buildPassed}
        testsPassCount={testsPassCount}
        testsFailCount={testsFailCount}
        failingSummary={failingSummary}
      />
      <CodeReview
        nodeId={`${phaseId}:code-review`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={whatWasDone}
        buildPassed={buildPassed}
        failingSummary={failingSummary}
      />
    </Parallel>
  );
}
