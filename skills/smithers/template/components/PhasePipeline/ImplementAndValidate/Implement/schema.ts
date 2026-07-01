// Implement schema — output structure for the implementation step

import { z } from "zod";

export const ImplementSchema = z.object({
  /** Summary of what was implemented */
  summary: z.string(),
  /** Files created in this iteration */
  filesCreated: z.array(z.string()),
  /** Files modified in this iteration */
  filesModified: z.array(z.string()),
  /** Git commit messages made */
  commitMessages: z.array(z.string()),
  /** What was accomplished */
  whatWasDone: z.string(),
  /** What still needs to be done (if incomplete) */
  nextSteps: z.string().nullable(),
  /** Whether implementation is believed complete */
  believesComplete: z.boolean(),
});

export type ImplementOutput = z.infer<typeof ImplementSchema>;
