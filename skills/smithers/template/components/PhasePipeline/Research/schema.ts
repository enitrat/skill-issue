// Research schema — output structure for the research step
//
// Rules:
// - Use .nullable() NEVER .optional() (OpenAI structured outputs rejects optional)

import { z } from "zod";

export const ResearchSchema = z.object({
  /** Path to written context file */
  contextFilePath: z.string(),
  /** Key findings from reference material */
  findings: z.array(z.string()),
  /** Reference files actually read */
  referencesRead: z.array(z.string()),
  /** Interfaces/function signatures discovered */
  interfacesFound: z.array(z.string()),
  /** Open questions or ambiguities */
  openQuestions: z.array(z.string()),
  /** Freeform notes for project-specific data */
  notes: z.string().nullable(),
});

export type ResearchOutput = z.infer<typeof ResearchSchema>;
