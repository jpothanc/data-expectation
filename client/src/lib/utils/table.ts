import type { TableData } from '../types';

/** Extracts an array of instrument records from various API response shapes. */
export function extractInstruments(responseData: unknown): Record<string, unknown>[] {
	if (Array.isArray(responseData)) {
		return responseData as Record<string, unknown>[];
	}
	if (responseData && typeof responseData === 'object') {
		const obj = responseData as Record<string, unknown>;
		if (Array.isArray(obj['instruments'])) {
			return obj['instruments'] as Record<string, unknown>[];
		}
		return [obj];
	}
	return [];
}

/** Converts an array of arbitrary objects to a flat TableData structure. */
export function convertToTableData(items: Record<string, unknown>[]): TableData {
	if (items.length === 0) return { data: [], headers: [] };

	const allKeys = new Set<string>();
	for (const item of items) {
		if (item && typeof item === 'object') {
			for (const key of Object.keys(item)) allKeys.add(key);
		}
	}

	return {
		data: items.map((item) => normaliseRow(item, Array.from(allKeys))),
		headers: Array.from(allKeys),
	};
}

/** Converts instruments to a TableData with prioritised, sorted column headers. */
export function convertInstrumentsToTableData(instruments: Record<string, unknown>[]): TableData {
	if (instruments.length === 0) return { data: [], headers: [] };

	const allKeys = new Set<string>();
	for (const item of instruments) {
		if (item && typeof item === 'object') {
			for (const key of Object.keys(item)) allKeys.add(key);
		}
	}

	const priority = ['RIC', 'Symbol', 'IssuerName', 'Exchange', 'SecurityType', 'TradingStatus', 'Currency'];
	const headers = [
		...priority.filter((f) => allKeys.has(f)),
		...Array.from(allKeys).filter((f) => !priority.includes(f)).sort(),
	];

	return {
		data: instruments.map((item) => normaliseRow(item, headers)),
		headers,
	};
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

function normaliseRow(item: Record<string, unknown>, headers: string[]): Record<string, string> {
	const row: Record<string, string> = {};
	for (const header of headers) {
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
	}
	return row;
}
