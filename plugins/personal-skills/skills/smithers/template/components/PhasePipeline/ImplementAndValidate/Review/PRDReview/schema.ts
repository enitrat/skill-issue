// PRDReview schema — output structure for the spec/PRD review step

import { z } from "zod";
import { issueSchema } from "../../shared.js";

export const PRDReviewSchema = z.object({
  /** Overall severity of findings */
  severity: z.enum(["critical", "major", "minor", "none"]),
  /** Whether implementation matches spec */
  approved: z.boolean(),
  /** Issues found */
  issues: z.array(issueSchema),
  /** Spec coverage assessment */
  specCoverage: z.string(),
  /** Overall feedback */
  feedback: z.string(),
  /** Freeform notes for project-specific data */
  notes: z.string().nullable(),
});

export type PRDReviewOutput = z.infer<typeof PRDReviewSchema>;
