import type { ValidationResult } from '../types';
import { formatExpectationType, formatHeaderName } from './formatters';
import { extractResultDetails, parseResultObject } from './validation';

/**
 * Preferred column order for validation table
 */
const VALIDATION_COLUMN_ORDER = [
	'status',
	'column',
	'expectationType',
	'element_count',
	'unexpected_count',
	'unexpected_percent',
	'unexpected_percent_total',
	'unexpected_percent_nonmissing',
	'missing_count',
	'missing_percent',
	'partial_unexpected_list',
	'partial_unexpected_counts',
	'partial_unexpected_index_list'
] as const;

/**
 * Columns to hide from the validation table
 */
const HIDDEN_COLUMNS = [
	'partial_unexpected_list',
	'partial_unexpected_index_list',
	'unexpected_percent_total',
	'unexpected_percent_nonmissing',
	'missing_count',
	'missing_percent'
] as const;

/**
 * Transforms validation results into table data format
 */
export function transformValidationResultsToTableData(
	results: ValidationResult[]
): { data: Array<Record<string, any>>; headers: string[] } {
	if (results.length === 0) {
		return { data: [], headers: [] };
	}

	// Collect all possible headers from all results
	const allHeaders = new Set<string>(['status', 'column', 'expectationType']);

	const data = results.map(result => {
		// Parse the result object
		const { resultDetails, resultString } = parseResultObject(result);

		// Extract all relevant details from result object
		const details = extractResultDetails(resultDetails, resultString || undefined);

		// Also check top-level properties of ValidationResult that might not be in the result string
		// This is important for custom rule validations where some fields might be at the top level
		// Merge top-level properties that aren't already in details
		const topLevelFields: (keyof ValidationResult)[] = ['element_count'];
		topLevelFields.forEach(field => {
			if (result[field] !== undefined && details[field] === undefined) {
				details[field] = result[field];
			}
		});

		// Add detail field names to headers set
		Object.keys(details).forEach(key => allHeaders.add(key));

		return {
			status: result.success ? '✓' : '✗',
			column: result.column || 'N/A',
			expectationType: result.expectation_type ? formatExpectationType(result.expectation_type) : 'N/A',
			...details,
			_success: result.success
		};
	});

	// Convert headers set to array with preferred order, excluding hidden columns
	const headers = [
		...VALIDATION_COLUMN_ORDER.filter(h => allHeaders.has(h) && !HIDDEN_COLUMNS.includes(h as any)),
		...Array.from(allHeaders).filter(h => !VALIDATION_COLUMN_ORDER.includes(h as any) && !HIDDEN_COLUMNS.includes(h as any))
	];

	return { data, headers };
}

/**
 * Formats header names for display in the table
 */
export { formatHeaderName };

