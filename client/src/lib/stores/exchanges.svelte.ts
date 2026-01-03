import { getExchanges } from '../services/api';
import type { Exchange } from '../types';
import { DEFAULT_EXCHANGE } from '../constants';

/**
 * Shared reactive state for exchanges
 * Using module-level reactive variables for Svelte 5 compatibility
 */
let exchanges = $state<Exchange[]>([]);
let loading = $state(false);
let error = $state<string | null>(null);
let initialized = $state(false);

/**
 * Fetches exchanges from the API
 * Caches the result to avoid redundant API calls
 */
export async function fetchExchanges(): Promise<void> {
	// Return cached data if already initialized (even if empty, to prevent infinite loops)
	if (initialized) {
		return;
	}

	// Prevent concurrent fetches
	if (loading) {
		return;
	}

	loading = true;
	error = null;

	try {
		const fetchedExchanges = await getExchanges();
		exchanges = fetchedExchanges;
		initialized = true;
	} catch (err) {
		console.error('Failed to fetch exchanges:', err);
		error = err instanceof Error ? err.message : 'Failed to fetch exchanges';
		exchanges = [];
		initialized = true; // Mark as initialized even on error to prevent infinite retries
	} finally {
		loading = false;
	}
}

/**
 * Gets the default exchange value
 * Returns the first exchange if available, otherwise falls back to DEFAULT_EXCHANGE
 */
export function getDefaultExchange(): string {
	if (exchanges.length > 0) {
		return exchanges[0].value;
	}
	return DEFAULT_EXCHANGE;
}

/**
 * Finds an exchange by value
 */
export function findExchangeByValue(value: string): Exchange | undefined {
	return exchanges.find((e) => e.value === value);
}

/**
 * Gets exchange label by value
 */
export function getExchangeLabel(value: string): string {
	const exchange = findExchangeByValue(value);
	return exchange?.label || value;
}

/**
 * Resets the store (useful for testing or forced refresh)
 */
export function resetExchanges(): void {
	exchanges = [];
	loading = false;
	error = null;
	initialized = false;
}

/**
 * Exported store object for reactive access
 */
export const exchangesStore = {
	get exchanges() {
		return exchanges;
	},
	get loading() {
		return loading;
	},
	get error() {
		return error;
	},
	get initialized() {
		return initialized;
	},
	fetch: fetchExchanges,
	getDefaultExchange,
	findByValue: findExchangeByValue,
	getLabel: getExchangeLabel,
	reset: resetExchanges
};


