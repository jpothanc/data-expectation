/**
 * Timeout constants for API requests
 */
export const API_TIMEOUTS = {
	/** Standard API request timeout (15 seconds) */
	STANDARD: 15000,
	/** Extended timeout for complex operations (30 seconds) */
	EXTENDED: 30000,
	/** Quick timeout for fast operations (5 seconds) */
	QUICK: 5000
} as const;

