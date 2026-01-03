import type { ValidationResponse, ValidationResult } from '../types';

export interface PassFailCounts {
	passed: number;
	failed: number;
	total: number;
}

/**
 * Extracts pass/fail counts from validation response data
 * Handles multiple response structure formats
 */
export function getPassFailCounts(data: ValidationResponse | null): PassFailCounts {
	if (!data) return { passed: 0, failed: 0, total: 0 };

	// Try to get counts from summary fields first
	let passed = data.successful_expectations || 0;
	let failed = data.failed_expectations || 0;
	let total = data.total_expectations || 0;

	// If summary fields are not available, calculate from expectation results
	if (total === 0 && data.results?.expectation_results) {
		const results = data.results.expectation_results;
		passed = results.filter((r: any) => r.success === true).length;
		failed = results.filter((r: any) => r.success === false).length;
		total = results.length;
	}

	// Try results.summary as fallback
	if (total === 0 && data.results?.summary) {
		passed = data.results.summary.successful || 0;
		failed = data.results.summary.failed || 0;
		total = data.results.summary.total || passed + failed;
	}

	return { passed, failed, total };
}

/**
 * Filters validation results based on success status
 */
export function filterValidationResults(
	results: ValidationResult[],
	showFailedOnly: boolean
): ValidationResult[] {
	if (!showFailedOnly) {
		return results;
	}
	return results.filter((result) => !result.success);
}

/**
 * Parses a Python-style dictionary string (e.g., "{'key': np.int64(2)}") to JSON-compatible format
 */
function parsePythonDictString(str: string): any {
	try {
		// Step 1: Replace numpy types with their values
		// Replace np.int64(value) with just value (handles negative numbers too)
		str = str.replace(/np\.int64\((-?\d+)\)/g, '$1');
		// Replace np.float64(value) with just value (handles negative and scientific notation)
		str = str.replace(/np\.float64\((-?[\d.]+(?:[eE][+-]?\d+)?)\)/g, '$1');
		
		// Step 2: Handle Python literals
		str = str.replace(/\bNone\b/g, 'null');
		str = str.replace(/\bTrue\b/g, 'true');
		str = str.replace(/\bFalse\b/g, 'false');
		// Handle nan (not a number) - convert to null
		str = str.replace(/\bnan\b/g, 'null');
		
		// Step 3: Handle empty arrays first (before other replacements)
		// Empty arrays should already be valid JSON, but ensure they're properly formatted
		str = str.replace(/\[\s*\]/g, '[]');
		
		// Step 4: Convert dictionary keys first: 'key': -> "key":
		str = str.replace(/'([^']+)':/g, '"$1":');
		
		// Step 5: Handle arrays with content (must be done before handling string values)
		// Match arrays like [1001, 1001] or [{'value': 1001, 'count': 2}]
		str = str.replace(/\[([^\]]+)\]/g, (match, content) => {
			// Trim whitespace
			content = content.trim();
			
			// If empty array, return as is
			if (!content) {
				return '[]';
			}
			
			// If content contains dictionary-like structures, handle them
			if (content.includes('{')) {
				// Replace single quotes in nested dicts (keys already converted, handle values)
				content = content.replace(/:\s*'([^']+)'/g, (m, val) => {
					// Handle nan
					if (val === 'nan') {
						return ': null';
					}
					// Check if it's a number
					if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(val)) {
						return `: ${val}`;
					}
					return `: "${val}"`;
				});
				// Also handle unquoted nan values in dict values (e.g., 'value': nan)
				content = content.replace(/:\s*nan\b/g, ': null');
			} else {
				// Simple array - process each item
				content = content.split(',').map(item => {
					item = item.trim();
					// Remove surrounding single quotes if present
					if (item.startsWith("'") && item.endsWith("'")) {
						item = item.slice(1, -1);
					}
					// Handle nan (should already be converted to null in Step 2, but check just in case)
					if (item === 'nan') {
						return 'null';
					}
					// Check if it's a number
					if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(item)) {
						return item;
					}
					// Check if it's already a boolean/null
					if (item === 'true' || item === 'false' || item === 'null') {
						return item;
					}
					// Otherwise quote it
					return `"${item}"`;
				}).join(', ');
			}
			return `[${content}]`;
		});
		
		// Step 6: Handle remaining string values outside arrays (but preserve numbers, booleans, null)
		// Match : 'value' patterns that aren't already in arrays
		str = str.replace(/:\s*'([^']+)'/g, (match, value) => {
			// Check if it's a number (including negative and decimal)
			if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(value)) {
				return `: ${value}`;
			}
			// Check if it's a boolean or null (already converted)
			if (value === 'true' || value === 'false' || value === 'null') {
				return `: ${value}`;
			}
			// Otherwise, it's a string - quote it
			return `: "${value}"`;
		});
		
		// Step 7: Parse as JSON
		return JSON.parse(str);
	} catch (error) {
		console.warn('Failed to parse Python dict string:', error, 'Original string:', str);
		// If parsing still fails, return empty object
		return {};
	}
}

/**
 * Parses a validation result object to extract result details
 */
export function parseResultObject(result: ValidationResult): {
	resultDetails: any;
	resultString: string | null;
} {
	const resultString = result.result || null;
	let resultDetails: any = {};

	if (resultString) {
		try {
			if (typeof resultString === 'string') {
				// First try standard JSON parsing
				try {
					resultDetails = JSON.parse(resultString);
				} catch {
					// If that fails, try parsing as Python-style dict string
					resultDetails = parsePythonDictString(resultString);
				}
			} else if (typeof resultString === 'object') {
				// If result is already an object, use it directly
				resultDetails = resultString;
			} else {
				resultDetails = {};
			}
		} catch {
			// If all parsing fails, try Python-style parsing as fallback
			if (typeof resultString === 'string') {
				resultDetails = parsePythonDictString(resultString);
			} else if (typeof resultString === 'object') {
				resultDetails = resultString;
			} else {
				resultDetails = {};
			}
		}
	}

	return { resultDetails, resultString: typeof resultString === 'string' ? resultString : JSON.stringify(resultString) };
}

/**
 * Extracts detailed information from result object
 */
export function extractResultDetails(
	resultDetails: any,
	resultString?: string
): Record<string, any> {
	const details: Record<string, any> = {};

	if (!resultDetails || typeof resultDetails !== 'object') {
		return details;
	}

	// Extract all fields from resultDetails
	// Start with common fields
	if (resultDetails.element_count !== undefined) {
		details.element_count = resultDetails.element_count;
	}
	if (resultDetails.unexpected_count !== undefined) {
		details.unexpected_count = resultDetails.unexpected_count;
	}
	if (resultDetails.unexpected_percent !== undefined) {
		details.unexpected_percent = resultDetails.unexpected_percent;
	}
	if (resultDetails.unexpected_percent_total !== undefined) {
		details.unexpected_percent_total = resultDetails.unexpected_percent_total;
	}
	if (resultDetails.unexpected_percent_nonmissing !== undefined) {
		details.unexpected_percent_nonmissing = resultDetails.unexpected_percent_nonmissing;
	}
	if (resultDetails.partial_unexpected_list !== undefined) {
		details.partial_unexpected_list = JSON.stringify(resultDetails.partial_unexpected_list);
	}
	if (resultDetails.partial_unexpected_counts !== undefined) {
		details.partial_unexpected_counts = JSON.stringify(resultDetails.partial_unexpected_counts);
	}
	if (resultDetails.partial_unexpected_index_list !== undefined) {
		details.partial_unexpected_index_list = JSON.stringify(resultDetails.partial_unexpected_index_list);
	}
	if (resultDetails.missing_count !== undefined) {
		details.missing_count = resultDetails.missing_count;
	}
	if (resultDetails.missing_percent !== undefined) {
		details.missing_percent = resultDetails.missing_percent;
	}

	// Add any other fields
	Object.keys(resultDetails).forEach((key) => {
		if (!details.hasOwnProperty(key)) {
			const value = resultDetails[key];
			if (value !== null && value !== undefined) {
				if (typeof value === 'object') {
					details[key] = JSON.stringify(value);
				} else {
					details[key] = value;
				}
			}
		}
	});

	return details;
}
