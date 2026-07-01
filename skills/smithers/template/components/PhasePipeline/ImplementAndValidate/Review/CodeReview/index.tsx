// CodeReview — Code quality, conventions, security review

import { Task, outputs } from "../../../../../smithers.js";
import { makeCodeReviewer } from "../../../../../agents.js";
import { renderInstructions } from "../../../../../utils.js";
import CodeReviewPrompt from "./prompt.mdx";

interface CodeReviewProps {
  nodeId: string;
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  filesCreated: string;
  filesModified: string;
  whatWasDone: string;
  buildPassed: boolean;
  failingSummary: string | null;
}

export function CodeReview({
  nodeId,
  phaseId,
  phaseName,
  phaseMetadata,
  filesCreated,
  filesModified,
  whatWasDone,
  buildPassed,
  failingSummary,
}: CodeReviewProps) {
  const projectInstructions = renderInstructions("code-review", phaseMetadata);

  return (
    <Task
      id={nodeId}
      output={outputs.code_review}
      agent={makeCodeReviewer()}
      timeoutMs={600_000}
      continueOnFail
      retries={1}
    >
      <CodeReviewPrompt
        phaseId={phaseId}
        phaseName={phaseName}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={whatWasDone}
        buildPassed={String(buildPassed)}
        failingSummary={failingSummary ?? "none"}
        projectInstructions={projectInstructions}
      />
    </Task>
  );
}
