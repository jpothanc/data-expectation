/**
 * Column display configuration for the Failed Instruments modal.
 *
 * Keys are normalised product types (lowercase, singular: 'stock', 'option', 'future').
 * The failing column is always appended automatically if it isn't already present.
 * Any product type not listed here falls back to DEFAULT_COLUMNS.
 *
 * To add or reorder columns for a product type, edit the list for that type.
 * To add a new product type, add a new entry — no other files need changing.
 */

export const DEFAULT_COLUMNS: readonly string[] = [
	'MasterId',
	'RIC',
	'Sedol',
	'Exchange'
];

export const PRODUCT_TYPE_COLUMNS: Readonly<Record<string, readonly string[]>> = {
	stock: [
		'MasterId',
		'RIC',
		'Sedol',
		'Exchange',
		'Symbol',
		'SecurityType'
	],
	option: [
		'MasterId',
		'RIC',
		'Sedol',
		'Exchange',
		'Symbol',
		'UnderlyingRIC'
	],
	future: [
		'MasterId',
		'RIC',
		'Sedol',
		'Exchange',
		'Symbol',
		'ExpiryDate'
	]
};

/**
 * Return the ordered column list for a product type.
 * Falls back to DEFAULT_COLUMNS if the type has no specific entry.
 *
 * @param productType  Raw product type string (any casing, singular or plural).
 * @param failingColumn  The column that failed the expectation — always included.
 * @param availableKeys  Keys actually present in the instrument data — used to drop
 *                       configured columns the current data source doesn't have.
 */
export function getColumnsForProductType(
	productType: string,
	failingColumn: string,
	availableKeys: string[] = []
): string[] {
	const normalised = productType.toLowerCase().replace(/s$/, '');
	const configured = PRODUCT_TYPE_COLUMNS[normalised] ?? DEFAULT_COLUMNS;

	// Merge: configured columns + failing column, deduped, preserve order
	const merged = [...new Set([...configured, failingColumn])];

	// If we have real data, drop columns that don't exist in the payload
	if (availableKeys.length > 0) {
		return merged.filter((col) => availableKeys.includes(col));
	}

	return merged;
}
