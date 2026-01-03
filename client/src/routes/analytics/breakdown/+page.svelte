<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getTreemap, getExchangeValidationResults, type TreemapData, type ExchangeValidationResponse } from '$lib/services/api';
	import ExchangeResultsModal from '$lib/components/ExchangeResultsModal.svelte';
	import TreemapChart from '$lib/components/TreemapChart.svelte';
	import ChartCard from '$lib/components/ChartCard.svelte';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let days = $state(7);
	let isFetching = $state(false);
	let treemapData = $state<TreemapData[]>([]);
	
	let selectedExchange = $state<string | null>(null);
	let exchangeResults = $state<ExchangeValidationResponse | null>(null);
	let loadingExchangeResults = $state(false);

	// Get filter parameters from URL
	const filterRegion = $derived.by(() => $page.url.searchParams.get('region') || null);
	const filterProductType = $derived.by(() => $page.url.searchParams.get('productType') || null);

	// Filter treemap data based on query parameters
	const filteredTreemapData = $derived.by(() => {
		if (!filterRegion && !filterProductType) {
			return treemapData;
		}
		
		return treemapData.filter(item => {
			const matchesRegion = !filterRegion || item.Region === filterRegion;
			const matchesProductType = !filterProductType || item.ProductType === filterProductType;
			return matchesRegion && matchesProductType;
		});
	});

	async function fetchData() {
		if (isFetching) return;
		
		isFetching = true;
		loading = true;
		error = null;

		try {
			const withTimeout = <T>(promise: Promise<T>, timeoutMs: number): Promise<T> => {
				return Promise.race([
					promise,
					new Promise<T>((_, reject) => 
						setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
					)
				]);
			};
			
			const result = await withTimeout(getTreemap(days), 15000);
			treemapData = result.data;
		} catch (err) {
			console.error('Error fetching breakdown:', err);
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
			isFetching = false;
		}
	}


	async function handleExchangeClick(exchange: string) {
		if (selectedExchange === exchange || loadingExchangeResults) return;

		selectedExchange = exchange;
		exchangeResults = null;
		loadingExchangeResults = true;
		error = null;
		
		try {
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 30000);
			
			exchangeResults = await getExchangeValidationResults(exchange, days, undefined, controller.signal);
			
			clearTimeout(timeoutId);
		} catch (err) {
			console.error('Error fetching exchange results:', err);
			if (err instanceof Error) {
				error = err.name === 'AbortError' 
					? 'Request timed out. Please try again.'
					: err.message || 'Failed to load exchange results';
			} else {
				error = 'Failed to load exchange results';
			}
			exchangeResults = null;
		} finally {
			loadingExchangeResults = false;
		}
	}

	function closeModal() {
		selectedExchange = null;
		exchangeResults = null;
		loadingExchangeResults = false;
	}

	let initialFetchDone = $state(false);
	
	$effect(() => {
		if (!initialFetchDone) {
			initialFetchDone = true;
			setTimeout(() => {
				fetchData().catch(err => {
					console.error('Error in initial fetch:', err);
					loading = false;
					isFetching = false;
					error = err instanceof Error ? err.message : 'Failed to load data';
				});
			}, 0);
		}
	});
</script>

<div class="page-container">
	<div class="page-controls">
		<div class="control-group">
			<label for="days">Period:</label>
			<select id="days" bind:value={days} onchange={fetchData}>
				<option value={7}>7 Days</option>
				<option value={14}>14 Days</option>
				<option value={30}>30 Days</option>
			</select>
		</div>
		<button class="refresh-button" onclick={fetchData} disabled={loading} type="button" title="Refresh data">
			{#if loading}
				<svg class="refresh-icon spinning" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			{:else}
				<svg class="refresh-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			{/if}
		</button>
	</div>
	
	{#if filterRegion || filterProductType}
		<div class="filter-badge">
			Filtered: {filterRegion || 'All Regions'} × {filterProductType || 'All Products'}
		</div>
	{/if}

	{#if error}
		<div class="error">
			<p>Error: {error}</p>
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading breakdown data...</p>
		</div>
	{:else}
		<div class="chart-container">
			{#if filterRegion || filterProductType}
				<div class="filter-badge">
					<span>Filtered by: {filterRegion || 'All'} × {filterProductType || 'All'}</span>
					<button 
						class="clear-filter-btn"
						onclick={() => goto('/analytics/breakdown')}
						type="button"
						title="Clear filters"
					>
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			{/if}
			<ChartCard title="Regional Exchange Breakdown" stats={[
				{ label: 'Exchanges', value: filteredTreemapData.length },
				{ label: 'Total', value: treemapData.length }
			]}>
				{#if filteredTreemapData.length > 0}
					<TreemapChart data={filteredTreemapData} onExchangeClick={handleExchangeClick} />
				{:else if treemapData.length > 0}
					<div class="no-data-message">
						<p>No data available for the selected filters</p>
					</div>
				{:else}
					<div class="no-data-message">
						<p>No data available</p>
					</div>
				{/if}
			</ChartCard>
		</div>
	{/if}

	{#if selectedExchange}
		{#if loadingExchangeResults}
			<div class="modal-overlay" onclick={closeModal} role="dialog" aria-modal="true">
				<div class="modal-content loading-modal" onclick={(e) => e.stopPropagation()}>
					<div class="spinner"></div>
					<p>Loading validation results for {selectedExchange}...</p>
				</div>
			</div>
		{:else if exchangeResults}
			<ExchangeResultsModal
				exchange={selectedExchange}
				results={exchangeResults.runs}
				onClose={closeModal}
			/>
		{/if}
	{/if}
</div>

<style>
	.page-container {
		max-width: 1600px;
		margin: 0 auto;
		padding: 1.25rem 2rem;
		min-height: calc(100vh - 60px);
	}

	.page-controls {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 0.75rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}
	
	.filter-badge {
		padding: 0.5rem 1rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		font-size: 0.75rem;
		margin-bottom: 1rem;
		display: inline-block;
	}

	.control-group {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.control-group label {
		font-size: 0.75rem;
		color: #9ca3af;
		font-weight: 500;
		white-space: nowrap;
	}

	.control-group select {
		padding: 0.375rem 0.625rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #e5e7eb;
		font-size: 0.75rem;
		cursor: pointer;
		transition: border-color 0.2s;
	}

	.refresh-button {
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #9ca3af;
		padding: 0.4375rem 0.75rem;
		border-radius: 0.375rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		width: 2.25rem;
		height: 2.25rem;
	}

	.refresh-button:hover:not(:disabled) {
		background-color: #059669;
		border-color: #059669;
		color: white;
	}

	.refresh-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		background: #374151;
	}

	.refresh-icon {
		width: 1rem;
		height: 1rem;
	}

	.refresh-icon.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error {
		margin-top: 1.5rem;
		padding: 1rem;
		background-color: #7f1d1d;
		border: 1px solid #dc2626;
		border-radius: 0.5rem;
		color: #fca5a5;
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 4rem 2rem;
		gap: 1rem;
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #374151;
		border-top-color: #34d399;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.chart-container {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1.5rem;
	}

	.filter-badge {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background-color: rgba(16, 185, 129, 0.1);
		border: 1px solid rgba(16, 185, 129, 0.3);
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}

	.filter-badge span {
		font-size: 0.875rem;
		color: #93c5fd;
		font-weight: 500;
	}

	.clear-filter-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 1.75rem;
		height: 1.75rem;
		padding: 0;
		background-color: transparent;
		border: 1px solid rgba(16, 185, 129, 0.3);
		border-radius: 0.375rem;
		color: #93c5fd;
		cursor: pointer;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.clear-filter-btn:hover {
		background-color: rgba(16, 185, 129, 0.2);
		border-color: #34d399;
		color: #34d399;
	}

	.clear-filter-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.no-data-message {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 150px;
		color: #6b7280;
		font-size: 0.875rem;
		background: rgba(55, 65, 81, 0.3);
		border-radius: 0.5rem;
		border: 1px dashed #374151;
	}

	.modal-overlay {
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
	}

	.modal-content {
		background-color: #1f2937;
		border-radius: 0.75rem;
		padding: 2rem;
		max-width: 90vw;
		max-height: 90vh;
		overflow-y: auto;
		border: 1px solid #374151;
	}

	.loading-modal {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		min-width: 300px;
	}

	@media (max-width: 768px) {
		.page-container {
			padding: 1rem;
		}
	}
</style>


