/**
 * Promise utilities for handling timeouts and race conditions
 */

/**
 * Wraps a promise with a timeout
 * @param promise The promise to wrap
 * @param timeoutMs Timeout in milliseconds
 * @returns Promise that rejects if timeout is reached
 */
export function withTimeout<T>(
	promise: Promise<T>,
	timeoutMs: number
): Promise<T> {
	return Promise.race([
		promise,
		new Promise<T>((_, reject) =>
			setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
		)
	]);
}

/**
 * Executes multiple promises with timeout and returns settled results
 * @param promises Array of promises to execute
 * @param timeoutMs Timeout in milliseconds for each promise
 * @returns Promise that resolves to array of settled results
 */
export async function allSettledWithTimeout<T>(
	promises: Promise<T>[],
	timeoutMs: number
): Promise<PromiseSettledResult<T>[]> {
	const timeoutPromises = promises.map(p => withTimeout(p, timeoutMs));
	return Promise.allSettled(timeoutPromises);
}

