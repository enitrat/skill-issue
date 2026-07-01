// FinalReview schema — output structure for the gating decision

import { z } from "zod";

export const FinalReviewSchema = z.object({
  /** THE GATE FLAG — should we move to the next phase? */
  readyToMoveOn: z.boolean(),
  /** Reasoning for the decision — fed back to next pass's Implement step */
  reasoning: z.string(),
  /** Overall approval */
  approved: z.boolean(),
  /** Quality score 1-10 */
  qualityScore: z.number().min(1).max(10),
  /** Remaining issues preventing approval */
  remainingIssues: z.array(
    z.object({
      severity: z.enum(["critical", "major", "minor"]),
      description: z.string(),
      file: z.string().nullable(),
    }),
  ),
});

export type FinalReviewOutput = z.infer<typeof FinalReviewSchema>;
