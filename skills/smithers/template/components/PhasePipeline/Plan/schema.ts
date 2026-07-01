// Plan schema — output structure for the planning step

import { z } from "zod";

export const PlanSchema = z.object({
  /** Path to written plan file */
  planFilePath: z.string(),
  /** Ordered implementation steps (atomic units of work) */
  implementationSteps: z.array(z.string()),
  /** Files that will be created */
  filesToCreate: z.array(z.string()),
  /** Files that will be modified */
  filesToModify: z.array(z.string()),
  /** Dependencies on other phases */
  dependencies: z.array(z.string()),
  /** Estimated complexity */
  complexity: z.enum(["trivial", "small", "medium", "large"]),
});

export type PlanOutput = z.infer<typeof PlanSchema>;
