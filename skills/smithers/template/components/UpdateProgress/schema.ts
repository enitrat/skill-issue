// UpdateProgress schema — output structure for progress tracking

import { z } from "zod";

export const ProgressSchema = z.object({
  /** Updated progress markdown content */
  progressMarkdown: z.string(),
  /** Per-phase completion percentages */
  phaseCompletion: z.array(
    z.object({
      phaseId: z.string(),
      phaseName: z.string(),
      completionPercent: z.number().min(0).max(100),
      done: z.string(),
      missing: z.string(),
    }),
  ),
  /** Overall completion percentage */
  overallCompletion: z.number().min(0).max(100),
});

export type ProgressOutput = z.infer<typeof ProgressSchema>;
