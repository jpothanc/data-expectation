/**
 * Formats expectation type from camelCase to readable format
 * Example: "ExpectColumnValuesToBeInSet" -> "Column Values To Be In Set"
 */
export function formatExpectationType(type: string): string {
	return type
		.replace(/^Expect/, '')
		.replace(/([A-Z])/g, ' $1')
		.trim();
}

/**
 * Formats header name from snake_case to PascalCase
 * Example: "unexpected_count" -> "Unexpected Count"
 */
export function formatHeaderName(header: string): string {
	return header
		.split('_')
		.map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
		.join(' ');
}

