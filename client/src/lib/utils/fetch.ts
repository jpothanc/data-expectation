/**
 * Data fetching utilities with loading and error state management
 */

export interface FetchState {
	loading: boolean;
	error: string | null;
	isFetching: boolean;
}

export interface FetchOptions {
	timeout?: number;
	onError?: (error: Error) => void;
}

/**
 * Creates a fetch function with loading/error state management
 */
export function createFetchHandler<T>(
	state: FetchState,
	fetchFn: () => Promise<T>,
	options: FetchOptions = {}
): () => Promise<T | null> {
	const { timeout = 15000, onError } = options;

	return async (): Promise<T | null> => {
		if (state.isFetching) return null;

		state.isFetching = true;
		state.loading = true;
		state.error = null;

		try {
			const result = await fetchFn();
			return result;
		} catch (err) {
			const error = err instanceof Error ? err : new Error('An unknown error occurred');
			state.error = error.message;
			
			if (onError) {
				onError(error);
			} else {
				console.error('Error fetching data:', error);
			}
			
			return null;
		} finally {
			state.loading = false;
			state.isFetching = false;
		}
	};
}

