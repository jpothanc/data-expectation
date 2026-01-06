<script lang="ts">
	import { getRegionalTrends, type RegionalTrendResponse } from '$lib/services/api';
	import { withTimeout } from '$lib/utils/promise';
	import { API_TIMEOUTS } from '$lib/constants/timeouts';
	import { DEFAULT_PERIOD } from '$lib/constants/periods';
	import PageControls from '$lib/components/PageControls.svelte';
	import LineChart from '$lib/components/LineChart.svelte';
	import HeatmapChart from '$lib/components/HeatmapChart.svelte';
	import SparklinesChart from '$lib/components/SparklinesChart.svelte';
	import StackedAreaChart from '$lib/components/StackedAreaChart.svelte';
	import ChartCard from '$lib/components/ChartCard.svelte';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let days = $state(30);
	let isFetching = $state(false);
	let regionalTrendsData = $state<RegionalTrendResponse | null>(null);
	let activeTab = $state<'line' | 'heatmap' | 'sparklines' | 'stacked'>('line');

	async function fetchData() {
		if (isFetching) return;
		
		isFetching = true;
		loading = true;
		error = null;

		try {
			const result = await withTimeout(
				getRegionalTrends(Math.max(days, 30)),
				API_TIMEOUTS.STANDARD
			);
			regionalTrendsData = result;
		} catch (err) {
			console.error('Error fetching trends:', err);
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
			isFetching = false;
		}
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
	<div class="page-header">
		<h1 class="page-title">Trends</h1>
	</div>
	<PageControls days={days} onDaysChange={(d) => { days = d; fetchData(); }} onRefresh={fetchData} {loading} />

	{#if error}
		<div class="error">
			<p>Error: {error}</p>
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading trend data...</p>
		</div>
	{:else}
		<div class="tabs-container">
			<div class="tabs">
				<button 
					class="tab-button {activeTab === 'line' ? 'active' : ''}"
					onclick={() => activeTab = 'line'}
					type="button"
				>
					Line Chart
				</button>
				<button 
					class="tab-button {activeTab === 'heatmap' ? 'active' : ''}"
					onclick={() => activeTab = 'heatmap'}
					type="button"
				>
					Heatmap
				</button>
				<button 
					class="tab-button {activeTab === 'sparklines' ? 'active' : ''}"
					onclick={() => activeTab = 'sparklines'}
					type="button"
				>
					Sparklines
				</button>
				<button 
					class="tab-button {activeTab === 'stacked' ? 'active' : ''}"
					onclick={() => activeTab = 'stacked'}
					type="button"
				>
					Stacked Area
				</button>
			</div>

			<div class="chart-container">
				{#if regionalTrendsData && Object.keys(regionalTrendsData.data).length > 0}
					{#if activeTab === 'line'}
						<ChartCard title="Failure Trends by Region (Line Chart)" stats={[
							{ label: 'Data Points', value: Object.values(regionalTrendsData.data).flat().length },
							{ label: 'Regions', value: Object.keys(regionalTrendsData.data).length },
							{ label: 'Total Failures', value: Object.values(regionalTrendsData.data).flat().reduce((sum, d) => sum + (d.FailedRuns || 0), 0) }
						]}>
							<LineChart data={regionalTrendsData.data} height="500px" />
						</ChartCard>
					{:else if activeTab === 'heatmap'}
						<ChartCard title="Failure Trends Heatmap" stats={[
							{ label: 'Regions', value: Object.keys(regionalTrendsData.data).length },
							{ label: 'Time Periods', value: new Set(Object.values(regionalTrendsData.data).flat().map(d => d.Date)).size },
							{ label: 'Total Failures', value: Object.values(regionalTrendsData.data).flat().reduce((sum, d) => sum + (d.FailedRuns || 0), 0) }
						]}>
							<HeatmapChart data={regionalTrendsData.data} height="500px" days={days} />
						</ChartCard>
					{:else if activeTab === 'sparklines'}
						<ChartCard title="Regional Sparklines Overview" stats={[
							{ label: 'Regions', value: Object.keys(regionalTrendsData.data).length },
							{ label: 'Total Data Points', value: Object.values(regionalTrendsData.data).flat().length },
							{ label: 'Avg Success Rate', value: (Object.values(regionalTrendsData.data).flat().reduce((sum, d) => sum + (d.SuccessRate || 0), 0) / Object.values(regionalTrendsData.data).flat().length).toFixed(1) + '%' }
						]}>
							<SparklinesChart data={regionalTrendsData.data} height="500px" />
						</ChartCard>
					{:else if activeTab === 'stacked'}
						<ChartCard title="Cumulative Failure Trends (Stacked Area)" stats={[
							{ label: 'Regions', value: Object.keys(regionalTrendsData.data).length },
							{ label: 'Data Points', value: Object.values(regionalTrendsData.data).flat().length },
							{ label: 'Total Failures', value: Object.values(regionalTrendsData.data).flat().reduce((sum, d) => sum + (d.FailedRuns || 0), 0) }
						]}>
							<StackedAreaChart data={regionalTrendsData.data} height="500px" />
						</ChartCard>
					{/if}
				{:else}
					<div class="no-data-message">
						<p>No trend data available</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
		gap: 1rem;
	}

	.page-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
		color: #ffffff;
		letter-spacing: -0.02em;
	}

	.tabs-container {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.tabs {
		display: flex;
		gap: 0;
		border-bottom: 1px solid rgba(52, 211, 153, 0.08);
		padding-bottom: 0;
		overflow-x: auto;
		background-color: #111827;
	}

	/* Custom scrollbar styling with theme */
	.tabs::-webkit-scrollbar {
		height: 10px;
	}

	.tabs::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 5px;
	}

	.tabs::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.tabs::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	/* Firefox scrollbar */
	.tabs {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.tab-button {
		background: transparent;
		border: none;
		padding: 0.5rem 1rem;
		color: #9ca3af;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		border-bottom: 2px solid transparent;
		margin-bottom: -1px;
		white-space: nowrap;
	}

	.tab-button:hover {
		color: #e5e7eb;
		background-color: rgba(55, 65, 81, 0.3);
	}

	.tab-button.active {
		color: var(--color-primary-light);
		border-bottom-color: var(--color-primary-light);
		background-color: var(--color-border);
	}

	.chart-container {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1.5rem;
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

	.page-container {
		max-width: 1600px;
		margin: 0 auto;
		padding: 1.25rem 2rem;
		min-height: calc(100vh - 60px);
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

	@media (max-width: 768px) {
		.page-container {
			padding: 1rem;
		}
	}
</style>

