// Schema registry — collects all component schemas into a single map
//
// This is passed to createSmithers() to auto-generate SQLite tables.

import { ResearchSchema } from "./PhasePipeline/Research/schema.js";
import { PlanSchema } from "./PhasePipeline/Plan/schema.js";
import { ImplementSchema } from "./PhasePipeline/ImplementAndValidate/Implement/schema.js";
import { TestSchema } from "./PhasePipeline/ImplementAndValidate/Test/schema.js";
import { PRDReviewSchema } from "./PhasePipeline/ImplementAndValidate/Review/PRDReview/schema.js";
import { CodeReviewSchema } from "./PhasePipeline/ImplementAndValidate/Review/CodeReview/schema.js";
import { ReviewFixSchema } from "./PhasePipeline/ImplementAndValidate/ReviewFix/schema.js";
import { FinalReviewSchema } from "./PhasePipeline/FinalReview/schema.js";
import { PassTrackerSchema } from "./PassTracker/schema.js";
import { ProgressSchema } from "./UpdateProgress/schema.js";

export const outputSchemas = {
  research: ResearchSchema,
  plan: PlanSchema,
  implement: ImplementSchema,
  test_results: TestSchema,
  prd_review: PRDReviewSchema,
  code_review: CodeReviewSchema,
  review_fix: ReviewFixSchema,
  final_review: FinalReviewSchema,
  pass_tracker: PassTrackerSchema,
  progress: ProgressSchema,
};

// Re-export individual schemas for component imports
export {
  ResearchSchema,
  PlanSchema,
  ImplementSchema,
  TestSchema,
  PRDReviewSchema,
  CodeReviewSchema,
  ReviewFixSchema,
  FinalReviewSchema,
  PassTrackerSchema,
  ProgressSchema,
};
