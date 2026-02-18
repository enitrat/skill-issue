// PassTracker schema — records which pass just completed

import { z } from "zod";

export const PassTrackerSchema = z.object({
  totalIterations: z.number(),
  phasesRun: z.array(z.string()),
  phasesComplete: z.array(z.string()),
  summary: z.string(),
});

export type PassTrackerOutput = z.infer<typeof PassTrackerSchema>;
