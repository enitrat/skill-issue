// ReviewFix schema — output structure for the review fix step

import { z } from "zod";

export const ReviewFixSchema = z.object({
  /** Summary of what was fixed */
  summary: z.string(),
  /** Fixes applied */
  fixesMade: z.array(
    z.object({
      issue: z.string(),
      fix: z.string(),
      file: z.string().nullable(),
    }),
  ),
  /** Issues marked as false positives (with reasoning) */
  falsePositives: z.array(
    z.object({
      issue: z.string(),
      reasoning: z.string(),
    }),
  ),
  /** Whether all issues were resolved */
  allIssuesResolved: z.boolean(),
  /** Commit messages for fixes */
  commitMessages: z.array(z.string()),
});

export type ReviewFixOutput = z.infer<typeof ReviewFixSchema>;
