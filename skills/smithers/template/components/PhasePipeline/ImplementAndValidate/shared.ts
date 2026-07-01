// Shared sub-schemas used across validation loop components

import { z } from "zod";

export const issueSchema = z.object({
  severity: z.enum(["critical", "major", "minor"]),
  description: z.string(),
  file: z.string().nullable(),
  line: z.number().nullable(),
  suggestion: z.string().nullable(),
  /** Spec section, requirement ID, or other reference */
  reference: z.string().nullable(),
});

export type Issue = z.infer<typeof issueSchema>;
