<script lang="ts">
	import { formatHeaderName } from '../utils/formatters';

	interface Props {
		data: string;
		header: string;
		open: boolean;
		onClose: () => void;
	}

	let { data, header, open, onClose }: Props = $props();
	let searchText = $state('');

	function parsePartialData(jsonString: string): Array<{ value: string; count: number }> {
		try {
			const parsed = JSON.parse(jsonString);
			if (Array.isArray(parsed)) {
				return parsed.map((item: any) => {
					// Handle objects with value and count properties
					if (typeof item === 'object' && item !== null) {
						// Handle null values explicitly
						let valueStr: string;
						if (item.value === null || item.value === undefined) {
							valueStr = '(null)';
						} else if (item.key !== null && item.key !== undefined) {
							valueStr = String(item.key);
						} else {
							valueStr = String(item.value);
						}
						return {
							value: valueStr,
							count: typeof item.count === 'number' ? item.count : 1
						};
					}
					// Handle simple values (including null)
					if (item === null || item === undefined) {
						return {
							value: '(null)',
							count: 1
						};
					}
					return {
						value: String(item),
						count: 1
					};
				});
			}
			return [];
		} catch {
			return [];
		}
	}

	const parsedData = $derived(parsePartialData(data));

	// Sort by count (descending), then by value (ascending)
	const sortedData = $derived(
		[...parsedData].sort((a, b) => {
			if (b.count !== a.count) {
				return b.count - a.count; // Sort by count descending
			}
			return a.value.localeCompare(b.value); // Then by value ascending
		})
	);

	// Filter by search text
	const filteredData = $derived(
		searchText.trim()
			? sortedData.filter(item =>
					item.value.toLowerCase().includes(searchText.toLowerCase().trim())
			  )
			: sortedData
	);

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleEscape(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}
</script>

{#if open}
	<div
		class="modal-backdrop"
		onclick={handleBackdropClick}
		onkeydown={handleEscape}
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
	>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<div class="header-left">
					<h2 id="modal-title" class="modal-title">{formatHeaderName(header)}</h2>
					<span class="total-label">Total: {parsedData.length}</span>
				</div>
				<button class="close-button" onclick={onClose} type="button" aria-label="Close">
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="modal-body">
				{#if parsedData.length > 0}
					<div class="search-container">
						<label for="search-input" class="search-label">SEARCH:</label>
						<input
							id="search-input"
							type="text"
							bind:value={searchText}
							placeholder="Filter by value..."
							class="search-input"
						/>
						{#if searchText}
							<button
								class="clear-search-btn"
								onclick={() => (searchText = '')}
								type="button"
								title="Clear search"
							>
								<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						{/if}
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>VALUE</th>
									<th>COUNT</th>
								</tr>
							</thead>
							<tbody>
								{#if filteredData.length > 0}
									{#each filteredData as item}
										<tr>
											<td class="value-cell">{item.value}</td>
											<td class="count-cell">{item.count}</td>
										</tr>
									{/each}
								{:else}
									<tr>
										<td colspan="2" class="no-results">No results found matching "{searchText}"</td>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="no-data">No data available</p>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		max-width: 600px;
		width: 100%;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid #374151;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.modal-title {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #ffffff;
		margin: 0;
		line-height: 1.2;
	}

	.total-label {
		font-size: 0.8125rem;
		font-weight: 500;
		color: #9ca3af;
		line-height: 1.2;
	}

	.close-button {
		background: none;
		border: none;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 0.25rem;
		transition: all 0.2s;
	}

	.close-button:hover {
		background-color: #1f2937;
		color: #ffffff;
	}

	.close-button svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.modal-body {
		padding: 1rem 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		min-height: 0;
	}

	.search-container {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0.75rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
	}

	.search-label {
		font-size: 0.8125rem;
		font-weight: 500;
		color: #9ca3af;
		white-space: nowrap;
	}

	.search-input {
		flex: 1;
		padding: 0.4375rem 0.625rem;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.8125rem;
		background-color: #111827;
		color: #e5e7eb;
		transition: border-color 0.2s, box-shadow 0.2s;
	}

	.search-input::placeholder {
		color: #6b7280;
	}

	.search-input:hover:not(:disabled) {
		border-color: #34d399;
	}

	.search-input:focus {
		outline: none;
		border-color: #34d399;
		box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
	}

	.clear-search-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		padding: 0;
		background-color: transparent;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		cursor: pointer;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.clear-search-btn:hover {
		background-color: #374151;
		border-color: #34d399;
		color: #34d399;
	}

	.clear-search-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.table-container {
		flex: 1;
		overflow-y: auto;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		max-height: 400px;
		scrollbar-width: thin;
		scrollbar-color: #4b5563 #111827;
	}

	.table-container::-webkit-scrollbar {
		width: 12px;
	}

	.table-container::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 6px;
	}

	.table-container::-webkit-scrollbar-thumb {
		background: #4b5563;
		border-radius: 6px;
		border: 2px solid #111827;
	}

	.table-container::-webkit-scrollbar-thumb:hover {
		background: #6b7280;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
		background-color: #111827;
	}

	.data-table thead {
		background-color: #1f2937;
	}

	.data-table th {
		padding: 0.5rem 0.75rem;
		text-align: left;
		font-weight: 600;
		color: #e5e7eb;
		border-bottom: 2px solid #4b5563;
		font-size: 0.8125rem;
	}

	.data-table td {
		padding: 0.5rem 0.75rem;
		border-bottom: 1px solid #374151;
		color: #e5e7eb;
		font-size: 0.8125rem;
	}

	.data-table tbody tr:hover {
		background-color: #1f2937;
	}

	.data-table tbody tr:last-child td {
		border-bottom: none;
	}

	.value-cell {
		font-weight: 500;
		color: #34d399;
		font-family: 'Courier New', monospace;
	}

	.count-cell {
		text-align: right;
		font-weight: 600;
		color: #ffffff;
	}

	.no-data {
		color: #9ca3af;
		text-align: center;
		padding: 2rem;
		margin: 0;
	}

	.no-results {
		text-align: center;
		color: #9ca3af;
		padding: 2rem;
		font-style: italic;
	}

	.summary-label {
		font-weight: 600;
		color: #e5e7eb;
	}

	.summary-text {
		margin-top: 1rem;
		padding: 1rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-family: 'Courier New', monospace;
		font-size: 0.875rem;
		color: #e5e7eb;
		line-height: 1.6;
	}

	.summary-item {
		color: #34d399;
		font-weight: 500;
	}

	.separator {
		color: #6b7280;
	}
</style>

