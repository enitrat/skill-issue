// Test schema — output structure for the test step

import { z } from "zod";

export const TestSchema = z.object({
  /** Whether the build/compilation succeeded */
  buildPassed: z.boolean(),
  /** Whether all tests passed */
  testsPassed: z.boolean(),
  /** Number of tests passing */
  testsPassCount: z.number(),
  /** Number of tests failing */
  testsFailCount: z.number(),
  /** Failing test names and error messages */
  failingSummary: z.string().nullable(),
  /** Raw test output (truncated if too long) */
  testOutput: z.string(),
  /** Freeform notes for project-specific data */
  notes: z.string().nullable(),
});

export type TestOutput = z.infer<typeof TestSchema>;
