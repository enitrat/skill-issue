/**
 * Focus areas for the workflow.
 * TODO: Replace with 6-15 focus areas that cover your project's domains.
 *
 * Each focus becomes:
 * - A CategoryReview audit (one per loop iteration)
 * - An IntegrationTest suite (one per loop iteration)
 * - A bucket for ticket discovery to generate work in
 *
 * Guidelines:
 * - id: kebab-case unique identifier
 * - name: human-readable description (agents see this in prompts)
 * - Remove focuses once they reach production quality (saves agent time)
 */
export const focuses = [
	{ id: "core", name: "Core library and domain types" },
	{ id: "api", name: "API layer and HTTP routes" },
	{ id: "storage", name: "Database and persistence" },
	{ id: "auth", name: "Authentication and authorization" },
	{ id: "testing", name: "Test infrastructure and coverage" },
] as const;

export type FocusId = (typeof focuses)[number]["id"];
