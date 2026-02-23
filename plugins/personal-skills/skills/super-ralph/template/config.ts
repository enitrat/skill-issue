function parsePositiveInt(value: string | undefined, fallback: number): number {
	const parsed = Number.parseInt(value ?? "", 10);
	if (!Number.isFinite(parsed) || parsed <= 0) {
		return fallback;
	}
	return parsed;
}

export const WORKFLOW_MAX_CONCURRENCY = parsePositiveInt(
	process.env.WORKFLOW_MAX_CONCURRENCY,
	8,
);
export const WORKFLOW_TASK_RETRIES = parsePositiveInt(
	process.env.WORKFLOW_TASK_RETRIES,
	2,
);
