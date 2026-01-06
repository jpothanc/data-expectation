import { getExchanges } from '../services/api';
import type { Exchange } from '../types';
import { DEFAULT_EXCHANGE } from '../constants';

/**
 * Shared reactive state for exchanges per product type
 * Using module-level reactive variables for Svelte 5 compatibility
 */
let exchangesCache = $state<Record<string, Exchange[]>>({});
let loadingCache = $state<Record<string, boolean>>({});
let initializedCache = $state<Record<string, boolean>>({});
let error = $state<string | null>(null);

/**
 * Fetches exchanges from the API for a specific product type
 * Caches the result per product type to avoid redundant API calls
 */
export async function fetchExchanges(productType: string = 'stock'): Promise<void> {
	// Return cached data if already initialized for this product type
	if (initializedCache[productType]) {
		return;
	}

	// Prevent concurrent fetches for same product type
	if (loadingCache[productType]) {
		return;
	}

	loadingCache[productType] = true;
	error = null;

	try {
		const fetchedExchanges = await getExchanges(productType);
		exchangesCache[productType] = fetchedExchanges;
		initializedCache[productType] = true;
	} catch (err) {
		console.error(`Failed to fetch exchanges for ${productType}:`, err);
		error = err instanceof Error ? err.message : 'Failed to fetch exchanges';
		exchangesCache[productType] = [];
		initializedCache[productType] = true; // Mark as initialized even on error to prevent infinite retries
	} finally {
		loadingCache[productType] = false;
	}
}

/**
 * Gets the default exchange value for a specific product type
 * Returns the first exchange if available, otherwise falls back to DEFAULT_EXCHANGE
 */
export function getDefaultExchange(productType: string = 'stock'): string {
	const exchanges = exchangesCache[productType] || [];
	if (exchanges.length > 0) {
		return exchanges[0].value;
	}
	return DEFAULT_EXCHANGE;
}

/**
 * Finds an exchange by value for a specific product type
 */
export function findExchangeByValue(value: string, productType: string = 'stock'): Exchange | undefined {
	const exchanges = exchangesCache[productType] || [];
	return exchanges.find((e) => e.value === value);
}

/**
 * Gets exchange label by value for a specific product type
 */
export function getExchangeLabel(value: string, productType: string = 'stock'): string {
	const exchange = findExchangeByValue(value, productType);
	return exchange?.label || value;
}

/**
 * Resets the store for a specific product type (useful for testing or forced refresh)
 */
export function resetExchanges(productType?: string): void {
	if (productType) {
		exchangesCache[productType] = [];
		loadingCache[productType] = false;
		initializedCache[productType] = false;
	} else {
		exchangesCache = {};
		loadingCache = {};
		initializedCache = {};
	}
	error = null;
}

/**
 * Exported store object for reactive access
 */
export const exchangesStore = {
	getExchanges(productType: string = 'stock') {
		return exchangesCache[productType] || [];
	},
	isLoading(productType: string = 'stock') {
		return loadingCache[productType] || false;
	},
	isInitialized(productType: string = 'stock') {
		return initializedCache[productType] || false;
	},
	get error() {
		return error;
	},
	fetch: fetchExchanges,
	getDefaultExchange,
	findByValue: findExchangeByValue,
	getLabel: getExchangeLabel,
	reset: resetExchanges
};


