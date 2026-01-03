/**
 * Extracts instruments from various API response structures
 */
export function extractInstruments(responseData: any): any[] {
	// Handle different response structures
	if (Array.isArray(responseData)) {
		return responseData;
	} else if (responseData && typeof responseData === 'object') {
		// Check if response has an "instruments" property
		if (Array.isArray(responseData.instruments)) {
			return responseData.instruments;
		}
		// If it's a single instrument object, wrap it in an array
		return [responseData];
	}
	return [];
}

/**
 * Converts an array of items to table data format
 */
export function convertToTableData(items: any[]): { data: Array<Record<string, any>>; headers: string[] } {
	if (!Array.isArray(items) || items.length === 0) {
		return { data: [], headers: [] };
	}

	// Collect all unique keys from all items
	const allKeys = new Set<string>();
	items.forEach((item) => {
		if (typeof item === 'object' && item !== null) {
			Object.keys(item).forEach((key) => allKeys.add(key));
		}
	});

	return { data: items.map(item => ({ ...item })), headers: Array.from(allKeys) };
}

/**
 * Converts instruments array to table data with sorted headers
 */
export function convertInstrumentsToTableData(instruments: any[]): { data: Array<Record<string, any>>; headers: string[] } {
	if (!Array.isArray(instruments) || instruments.length === 0) {
		return { data: [], headers: [] };
	}

	// Collect all unique keys from all instruments
	const allKeys = new Set<string>();
	instruments.forEach((item) => {
		if (typeof item === 'object' && item !== null) {
			Object.keys(item).forEach((key) => allKeys.add(key));
		}
	});

	// Sort headers for better readability (put common fields first)
	const commonFields = ['RIC', 'Symbol', 'IssuerName', 'Exchange', 'SecurityType', 'TradingStatus', 'Currency'];
	const sortedHeaders = [
		...commonFields.filter(field => allKeys.has(field)),
		...Array.from(allKeys).filter(field => !commonFields.includes(field)).sort()
	];

	const headers = sortedHeaders.length > 0 ? sortedHeaders : Array.from(allKeys);
	const data = instruments.map((item) => {
		const row: Record<string, any> = {};
		headers.forEach((header) => {
			const value = item[header];
			if (value === null || value === undefined) {
				row[header] = '';
			} else if (typeof value === 'boolean') {
				row[header] = value ? 'Yes' : 'No';
			} else if (typeof value === 'object') {
				row[header] = JSON.stringify(value);
			} else {
				row[header] = String(value);
			}
		});
		return row;
	});

	return { data, headers };
}

