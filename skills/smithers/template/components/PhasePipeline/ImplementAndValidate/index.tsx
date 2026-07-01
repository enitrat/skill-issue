// ImplementAndValidate — Implement → Test → Review → Fix sequence
//
// Reads latest outputs from DB for iterative refinement.
// ReviewFix is skipped when both reviews approve.
// Note: this does NOT loop internally — iteration comes from the outer Ralph loop.
//
// All array → string formatting happens here, at the data boundary.
// Child components (Implement, Test, Review, ReviewFix) accept pre-formatted strings.

import { Sequence, useCtx } from "../../../smithers.js";
import { toStringArray } from "../../../utils.js";
import type { Issue } from "./shared.js";
import { Implement } from "./Implement/index.js";
import { Test } from "./Test/index.js";
import { Review } from "./Review/index.js";
import { ReviewFix } from "./ReviewFix/index.js";

interface ImplementAndValidateProps {
  phaseId: string;
  phaseName: string;
  phaseMetadata?: Record<string, unknown>;
  planFilePath: string;
  contextFilePath: string;
  implementationSteps: string[];
  pass: number;
}

/** Format an Issue[] (or JSON-encoded string) into a numbered list for MDX prompts. */
function formatIssues(issues: unknown, style: "prd" | "code"): string {
  let arr: Issue[];
  if (Array.isArray(issues)) {
    arr = issues as Issue[];
  } else if (typeof issues === "string") {
    try {
      arr = JSON.parse(issues) as Issue[];
    } catch {
      return "None";
    }
  } else {
    return "None";
  }
  if (!arr.length) return "None";
  return arr
    .map((i, n) =>
      style === "prd"
        ? `${n + 1}. [${i.severity}]${i.reference ? ` (${i.reference})` : ""} ${i.description}`
        : `${n + 1}. [${i.severity}] ${i.description}${i.file ? ` (${i.file})` : ""}`,
    )
    .join("\n");
}

export function ImplementAndValidate({
  phaseId,
  phaseName,
  phaseMetadata,
  planFilePath,
  contextFilePath,
  implementationSteps,
  pass,
}: ImplementAndValidateProps) {
  const ctx = useCtx();

  // Read latest outputs from previous iterations
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
  const latestFinalReview = ctx.outputMaybe("final_review", {
    nodeId: `${phaseId}:final-review`,
  });

  // Compute review feedback for next iteration
  const prdApproved = latestPRDReview?.severity === "none";
  const codeApproved = latestCodeReview?.severity === "none";
  const noReviewIssues = prdApproved && codeApproved;

  // Pre-format all array fields here — child components receive strings only
  const filesCreated = toStringArray(latestImpl?.filesCreated).join("\n- ");
  const filesModified = toStringArray(latestImpl?.filesModified).join("\n- ");
  const steps = toStringArray(implementationSteps)
    .map((s, i) => `${i + 1}. ${s}`)
    .join("\n");

  return (
    <Sequence>
      {/* 1. Implement (with feedback from previous iteration) */}
      <Implement
        nodeId={`${phaseId}:implement`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        planFilePath={planFilePath}
        contextFilePath={contextFilePath}
        implementationSteps={steps}
        previousSummary={latestImpl?.summary}
        previousNextSteps={latestImpl?.nextSteps ?? undefined}
        prdReviewFeedback={latestPRDReview?.feedback}
        codeReviewFeedback={latestCodeReview?.feedback}
        failingTests={
          latestTest && !latestTest.testsPassed
            ? (latestTest.failingSummary ?? latestTest.testOutput)
            : undefined
        }
        finalReviewFeedback={latestFinalReview?.reasoning}
        reviewFixSummary={latestReviewFix?.summary}
        pass={pass}
      />

      {/* 2. Test */}
      <Test
        nodeId={`${phaseId}:test`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={latestImpl?.whatWasDone ?? ""}
      />

      {/* 3. Parallel reviews */}
      <Review
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        filesCreated={filesCreated}
        filesModified={filesModified}
        whatWasDone={latestImpl?.whatWasDone ?? ""}
        buildPassed={latestTest?.buildPassed ?? false}
        testsPassed={latestTest?.testsPassed ?? false}
        testsPassCount={latestTest?.testsPassCount ?? 0}
        testsFailCount={latestTest?.testsFailCount ?? 0}
        failingSummary={latestTest?.failingSummary ?? null}
      />

      {/* 4. ReviewFix — skipped when both reviews approve */}
      <ReviewFix
        nodeId={`${phaseId}:review-fix`}
        phaseId={phaseId}
        phaseName={phaseName}
        phaseMetadata={phaseMetadata}
        prdIssues={formatIssues(latestPRDReview?.issues, "prd")}
        prdSeverity={latestPRDReview?.severity ?? "none"}
        codeIssues={formatIssues(latestCodeReview?.issues, "code")}
        codeSeverity={latestCodeReview?.severity ?? "none"}
        testsPassed={latestTest?.testsPassed ?? false}
        skipIf={noReviewIssues}
      />
    </Sequence>
  );
}
