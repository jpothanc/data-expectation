import type { ValidationResponse, ValidationResult } from '../types';

export interface PassFailCounts {
	passed: number;
	failed: number;
	total: number;
}

/** Extracts pass/fail counts from a validation response, handling multiple backend response shapes. */
export function getPassFailCounts(data: ValidationResponse | null): PassFailCounts {
	if (!data) return { passed: 0, failed: 0, total: 0 };

	let passed = data.successful_expectations ?? 0;
	let failed = data.failed_expectations ?? 0;
	let total = data.total_expectations ?? 0;

	if (total === 0 && data.results?.expectation_results) {
		const results = data.results.expectation_results;
		passed = results.filter((r) => r.success === true).length;
		failed = results.filter((r) => r.success === false).length;
		total = results.length;
	}

	if (total === 0 && data.results?.summary) {
		passed = data.results.summary.successful ?? 0;
		failed = data.results.summary.failed ?? 0;
		total = data.results.summary.total ?? passed + failed;
	}

	return { passed, failed, total };
}

/** Filters validation results by success status. */
export function filterValidationResults(
	results: ValidationResult[],
	showFailedOnly: boolean
): ValidationResult[] {
	return showFailedOnly ? results.filter((r) => !r.success) : results;
}

// ─── Python-dict → JSON parsing ───────────────────────────────────────────────

/**
 * Parses a Python-style dictionary string (e.g. "{'key': np.int64(2)}")
 * into a JSON-compatible value. Returns `{}` on parse failure.
 */
function parsePythonDictString(raw: string): Record<string, unknown> {
	try {
		let str = raw;
		// Numpy scalar wrappers
		str = str.replace(/np\.int64\((-?\d+)\)/g, '$1');
		str = str.replace(/np\.float64\((-?[\d.]+(?:[eE][+-]?\d+)?)\)/g, '$1');
		// Python literals → JSON literals
		str = str.replace(/\bNone\b/g, 'null');
		str = str.replace(/\bTrue\b/g, 'true');
		str = str.replace(/\bFalse\b/g, 'false');
		str = str.replace(/\bnan\b/g, 'null');
		// Normalise empty arrays
		str = str.replace(/\[\s*\]/g, '[]');
		// Dict keys: 'key': → "key":
		str = str.replace(/'([^']+)':/g, '"$1":');
		// Array contents
		str = str.replace(/\[([^\]]+)\]/g, (_match, content: string) => {
			content = content.trim();
			if (!content) return '[]';
			if (content.includes('{')) {
				content = content.replace(/:\s*'([^']+)'/g, (_m: string, val: string) => {
					if (val === 'nan') return ': null';
					if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(val)) return `: ${val}`;
					return `: "${val}"`;
				});
				content = content.replace(/:\s*nan\b/g, ': null');
			} else {
				content = content
					.split(',')
					.map((item) => {
						item = item.trim();
						if (item.startsWith("'") && item.endsWith("'")) item = item.slice(1, -1);
						if (item === 'nan') return 'null';
						if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(item)) return item;
						if (item === 'true' || item === 'false' || item === 'null') return item;
						return `"${item}"`;
					})
					.join(', ');
			}
			return `[${content}]`;
		});
		// Remaining string values outside arrays
		str = str.replace(/:\s*'([^']+)'/g, (_match, value: string) => {
			if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(value)) return `: ${value}`;
			if (value === 'true' || value === 'false' || value === 'null') return `: ${value}`;
			return `: "${value}"`;
		});
		return JSON.parse(str) as Record<string, unknown>;
	} catch (err) {
		console.warn('Failed to parse Python dict string:', err, 'Input:', raw);
		return {};
	}
}

// ─── Result parsing ───────────────────────────────────────────────────────────

export interface ParsedResult {
	resultDetails: Record<string, unknown>;
	resultString: string | null;
}

/** Parses the raw `result` field of a ValidationResult into a structured object. */
export function parseResultObject(result: ValidationResult): ParsedResult {
	const raw = result.result ?? null;
	let resultDetails: Record<string, unknown> = {};

	if (raw) {
		if (typeof raw === 'string') {
			try {
				resultDetails = JSON.parse(raw) as Record<string, unknown>;
			} catch {
				resultDetails = parsePythonDictString(raw);
			}
		} else if (typeof raw === 'object') {
			resultDetails = raw as Record<string, unknown>;
		}
	}

	return {
		resultDetails,
		resultString: typeof raw === 'string' ? raw : raw ? JSON.stringify(raw) : null,
	};
}

/** Extracts a flat display-ready details map from a parsed result object. */
export function extractResultDetails(
	resultDetails: Record<string, unknown>
): Record<string, unknown> {
	if (!resultDetails || typeof resultDetails !== 'object') return {};

	const KNOWN_FIELDS = [
		'element_count',
		'unexpected_count',
		'unexpected_percent',
		'unexpected_percent_total',
		'unexpected_percent_nonmissing',
		'missing_count',
		'missing_percent',
	];
	const SERIALISED_FIELDS = [
		'partial_unexpected_list',
		'partial_unexpected_counts',
		'partial_unexpected_index_list',
	];

	const details: Record<string, unknown> = {};

	for (const key of KNOWN_FIELDS) {
		if (resultDetails[key] !== undefined) details[key] = resultDetails[key];
	}
	for (const key of SERIALISED_FIELDS) {
		if (resultDetails[key] !== undefined) details[key] = JSON.stringify(resultDetails[key]);
	}

	// Append any remaining fields
	for (const [key, value] of Object.entries(resultDetails)) {
		if (!(key in details) && value != null) {
			details[key] = typeof value === 'object' ? JSON.stringify(value) : value;
		}
	}

	return details;
}
