// CodeReview schema — output structure for the code review step

import { z } from "zod";
import { issueSchema } from "../../shared.js";

export const CodeReviewSchema = z.object({
  /** Overall severity of findings */
  severity: z.enum(["critical", "major", "minor", "none"]),
  /** Whether code quality is acceptable */
  approved: z.boolean(),
  /** Issues found */
  issues: z.array(issueSchema),
  /** Code quality aspects */
  quality: z.object({
    conventions: z.enum(["pass", "fail"]),
    testCoverage: z.enum(["pass", "fail"]),
    errorHandling: z.enum(["pass", "fail"]),
    security: z.enum(["pass", "fail"]),
    tooling: z.enum(["pass", "fail"]),
  }),
  /** Overall feedback */
  feedback: z.string(),
});

export type CodeReviewOutput = z.infer<typeof CodeReviewSchema>;
