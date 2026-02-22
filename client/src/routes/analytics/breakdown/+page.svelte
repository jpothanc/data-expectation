<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { withTimeout } from '$lib/utils/promise';
	import { getTreemap, getExchangeValidationResults, type TreemapData, type ExchangeValidationResponse } from '$lib/services/api';
	import ExchangeResultsModal from '$lib/components/ExchangeResultsModal.svelte';
	import TreemapChart from '$lib/components/TreemapChart.svelte';
	import ChartCard from '$lib/components/ChartCard.svelte';
	import PageControls from '$lib/components/PageControls.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import ErrorBanner from '$lib/components/ErrorBanner.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let days = $state(7);
	let isFetching = $state(false);
	let treemapData = $state<TreemapData[]>([]);

	let selectedExchange = $state<string | null>(null);
	let exchangeResults = $state<ExchangeValidationResponse | null>(null);
	let loadingExchangeResults = $state(false);

	const filterRegion = $derived.by(() => $page.url.searchParams.get('region') || null);
	const filterProductType = $derived.by(() => $page.url.searchParams.get('productType') || null);

	const filteredTreemapData = $derived.by(() => {
		if (!filterRegion && !filterProductType) return treemapData;
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
	<PageControls {days} onDaysChange={(d) => { days = d; fetchData(); }} onRefresh={fetchData} {loading} />

	{#if error}
		<ErrorBanner message={error} />
	{/if}

	{#if loading}
		<LoadingState message="Loading breakdown data..." />
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
				{:else}
					<EmptyState message={treemapData.length > 0 ? 'No data for the selected filters' : 'No data available'} />
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
				passedRuns={exchangeResults.passed_runs ?? []}
				{days}
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

	.modal-overlay {
		position: fixed;
		inset: 0;
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

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #374151;
		border-top-color: #34d399;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@media (max-width: 768px) {
		.page-container {
			padding: 1rem;
		}
	}
</style>
