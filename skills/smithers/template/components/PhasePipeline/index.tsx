// PhasePipeline — Full lifecycle for a single phase
//
// Research → Plan → ValidationLoop → FinalReview
// Skipped if phase is already complete (readyToMoveOn: true)

import { Sequence, useCtx } from "../../smithers.js";
import { project } from "../../project.js";
import { toStringArray } from "../../utils.js";
import { Research } from "./Research/index.js";
import { Plan } from "./Plan/index.js";
import { ImplementAndValidate } from "./ImplementAndValidate/index.js";
import { FinalReview } from "./FinalReview/index.js";

interface PhasePipelineProps {
  phaseId: string;
  phaseName: string;
  phaseDescription: string;
  phaseMetadata?: Record<string, unknown>;
  pass: number;
  /** Whether this phase is already complete */
  skipIf: boolean;
}

export default function PhasePipeline({
  phaseId,
  phaseName,
  phaseDescription,
  phaseMetadata,
  pass,
  skipIf,
}: PhasePipelineProps) {
  const ctx = useCtx();

  // Read outputs from earlier steps in this phase
  const latestResearch = ctx.outputMaybe("research", {
    nodeId: `${phaseId}:research`,
  });
  const latestPlan = ctx.outputMaybe("plan", { nodeId: `${phaseId}:plan` });
  const latestImpl = ctx.outputMaybe("implement", {
    nodeId: `${phaseId}:implement`,
  });
  const latestTest = ctx.outputMaybe("test_results", {
    nodeId: `${phaseId}:test`,
  });
  const latestPRDReview = ctx.outputMaybe("prd_review", {
    nodeId: `${phaseId}:prd-review`,
  });
  const latestCodeReview = ctx.outputMaybe("code_review", {
    nodeId: `${phaseId}:code-review`,
  });
  const latestReviewFix = ctx.outputMaybe("review_fix", {
    nodeId: `${phaseId}:review-fix`,
  });

  // Resolve output paths from project config
  const contextPath = `${project.outputDir}/context/${phaseId}.md`;
  const planPath = `${project.outputDir}/plans/${phaseId}.md`;

  return (
    <Sequence skipIf={skipIf}>
      {/* 1. Research — gather reference material (once, not repeated) */}
      <Research
        nodeId={`${phaseId}:research`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseDescription={phaseDescription}
        phaseMetadata={phaseMetadata}
        outputPath={contextPath}
      />

      {/* 2. Plan — create implementation plan (once, not repeated) */}
      <Plan
        nodeId={`${phaseId}:plan`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseDescription={phaseDescription}
        phaseMetadata={phaseMetadata}
        contextFilePath={latestResearch?.contextFilePath ?? contextPath}
        findings={toStringArray(latestResearch?.findings).join("\n- ")}
        planOutputPath={planPath}
      />

      {/* 3. Implement + validate — Implement → Test → Review → Fix */}
      <ImplementAndValidate
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        planFilePath={latestPlan?.planFilePath ?? planPath}
        contextFilePath={latestResearch?.contextFilePath ?? contextPath}
        implementationSteps={latestPlan?.implementationSteps ?? []}
        pass={pass}
      />

      {/* 4. FinalReview — readyToMoveOn gating */}
      <FinalReview
        nodeId={`${phaseId}:final-review`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseDescription={phaseDescription}
        phaseMetadata={phaseMetadata}
        pass={pass}
        whatWasDone={latestImpl?.whatWasDone ?? ""}
        believesComplete={latestImpl?.believesComplete ?? false}
        buildPassed={latestTest?.buildPassed ?? false}
        testsPassCount={latestTest?.testsPassCount ?? 0}
        testsFailCount={latestTest?.testsFailCount ?? 0}
        prdReviewSeverity={latestPRDReview?.severity ?? "none"}
        prdReviewApproved={latestPRDReview?.approved ?? false}
        codeReviewSeverity={latestCodeReview?.severity ?? "none"}
        codeReviewApproved={latestCodeReview?.approved ?? false}
        allIssuesResolved={latestReviewFix?.allIssuesResolved}
      />
    </Sequence>
  );
}
