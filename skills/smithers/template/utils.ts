// utils.ts — Shared utilities for the workflow

import { project } from "./project.js";

/**
 * Safely coerce a DB value to a string array.
 *
 * ctx.outputMaybe() reads from SQLite where JSON arrays may be stored as TEXT
 * and returned as strings rather than parsed arrays. This handles all cases:
 *   - string[]    → pass-through
 *   - null / undefined → []
 *   - JSON-encoded string  → JSON.parse → string[]
 */
export function toStringArray(val: unknown): string[] {
  if (Array.isArray(val)) return val as string[];
  if (val == null) return [];
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed.startsWith("[")) {
      try {
        const parsed = JSON.parse(trimmed);
        return Array.isArray(parsed) ? (parsed as string[]) : [];
      } catch {
        // fall through
      }
    }
    return trimmed ? [trimmed] : [];
  }
  return [];
}

/**
 * Render a project instruction template for a given step and phase.
 * Returns empty string if the project doesn't provide instructions for this step.
 */
export function renderInstructions(
  stepName: string,
  phaseMetadata?: Record<string, unknown>,
): string {
  const template = project.instructions[stepName];
  if (!template) return "";

  // Convert metadata values to strings for MDX interpolation
  const props: Record<string, string> = {};
  if (phaseMetadata) {
    for (const [key, value] of Object.entries(phaseMetadata)) {
      if (Array.isArray(value)) {
        props[key] = value.join("\n- ");
      } else {
        props[key] = String(value ?? "");
      }
    }
  }

  return template(props);
}
