<script lang="ts">
	import StackedBarChart from '../StackedBarChart.svelte';
	import ProductHeatmapChart from '../ProductHeatmapChart.svelte';
	import DataTable from '../DataTable.svelte';
	import ChartCard from '../ChartCard.svelte';
	import ExpectationFailureModal from '../ExpectationFailureModal.svelte';
	import type { GlobalViewData, HeatmapData, ExpectationFailureByRegionData } from '$lib/services/api';

	interface Props {
		globalViewData: GlobalViewData[];
		heatmapData: HeatmapData[];
		expectationFailuresByRegionData?: ExpectationFailureByRegionData[];
		days?: number;
	}

	let { globalViewData, heatmapData, expectationFailuresByRegionData = [], days = 7 }: Props = $props();

	let selectedRegionFilter = $state<string | null>(null);
	let selectedProductTypeFilter = $state<string | null>(null);
	let selectedExpectationFailure = $state<Record<string, any> | null>(null);
	let showExpectationFailureModal = $state(false);

	function getExpectationTableData() {
		if (expectationFailuresByRegionData.length === 0) {
			return { headers: [], data: [] };
		}

		const headers = ['Region', 'ProductType', 'ColumnName', 'ExpectationType', 'FailureCount', 'TotalRuns', 'FailureRate'];
		
		// Filter by region and product type if filters are selected
		let filteredData = expectationFailuresByRegionData;
		if (selectedRegionFilter) {
			filteredData = filteredData.filter(d => d.Region === selectedRegionFilter);
		}
		if (selectedProductTypeFilter) {
			filteredData = filteredData.filter(d => d.ProductType?.toLowerCase() === selectedProductTypeFilter!.toLowerCase());
		}
		
		// Sort by Region, ProductType, then by FailureCount descending
		const sortedData = [...filteredData].sort((a, b) => {
			if (a.Region !== b.Region) {
				return a.Region.localeCompare(b.Region);
			}
			if (a.ProductType !== b.ProductType) {
				return (a.ProductType || '').localeCompare(b.ProductType || '');
			}
			return b.FailureCount - a.FailureCount;
		});

		// Format the data for the table
		const tableData = sortedData.map(item => ({
			Region: item.Region,
			ProductType: item.ProductType || 'N/A',
			ColumnName: item.ColumnName,
			ExpectationType: item.ExpectationType,
			FailureCount: item.FailureCount,
			TotalRuns: item.TotalRuns,
			FailureRate: typeof item.FailureRate === 'number' 
				? `${item.FailureRate.toFixed(1)}%` 
				: `${parseFloat(String(item.FailureRate || 0)).toFixed(1)}%`
		}));

		return { headers, data: tableData };
	}

	function handleRegionFilter(region: string | null) {
		selectedRegionFilter = region;
	}

	function handleProductTypeFilter(productType: string | null) {
		selectedProductTypeFilter = productType;
	}

	function handleRowClick(row: Record<string, any>, index: number) {
		selectedExpectationFailure = row;
		showExpectationFailureModal = true;
	}

	function closeExpectationFailureModal() {
		showExpectationFailureModal = false;
		selectedExpectationFailure = null;
	}

	// Get available regions from data
	const availableRegions = $derived.by(() => {
		return [...new Set(expectationFailuresByRegionData.map(d => d.Region))].sort();
	});

	// Get available product types from data
	const availableProductTypes = $derived.by(() => {
		return [...new Set(expectationFailuresByRegionData.map(d => d.ProductType).filter(Boolean))].sort();
	});
</script>

<div class="section-grid">
	<ChartCard title="Pass vs Fail by Region" stats={[
		{ label: 'Total Regions', value: globalViewData.length }
	]}>
		{#if globalViewData.length > 0}
			<StackedBarChart data={globalViewData} height="150px" />
		{:else}
			<div class="no-data-message">
				<p>No data available</p>
			</div>
		{/if}
	</ChartCard>

	<ChartCard title="Region x Product Success Rates" stats={[
		{ label: 'Data Points', value: heatmapData.length }
	]}>
		{#if heatmapData.length > 0}
			<ProductHeatmapChart data={heatmapData} days={days} height="500px" />
		{:else}
			<div class="no-data-message">
				<p>No data available</p>
			</div>
		{/if}
	</ChartCard>

	<ChartCard title="Expectation Failures by Region" stats={[
		{ label: 'Regions', value: [...new Set(expectationFailuresByRegionData.map(d => d.Region))].length },
		{ label: 'Expectations', value: [...new Set(expectationFailuresByRegionData.map(d => `${d.ColumnName} - ${d.ExpectationType}`))].length },
		{ label: 'Total Failures', value: expectationFailuresByRegionData.reduce((sum, d) => sum + d.FailureCount, 0) }
	]}>
		{#if expectationFailuresByRegionData.length > 0}
			<div class="table-filters">
				<div class="filter-group">
					<span class="filter-label">Region:</span>
					<button 
						class="filter-button {selectedRegionFilter === null ? 'active' : ''}"
						onclick={() => handleRegionFilter(null)}
						type="button"
					>
						All
					</button>
					{#each availableRegions as region}
						<button 
							class="filter-button {selectedRegionFilter === region ? 'active' : ''}"
							onclick={() => handleRegionFilter(region)}
							type="button"
						>
							{region}
						</button>
					{/each}
				</div>
				<div class="filter-group">
					<span class="filter-label">Product Type:</span>
					<button 
						class="filter-button {selectedProductTypeFilter === null ? 'active' : ''}"
						onclick={() => handleProductTypeFilter(null)}
						type="button"
					>
						All
					</button>
					{#each availableProductTypes as productType}
						<button 
							class="filter-button {selectedProductTypeFilter === productType ? 'active' : ''}"
							onclick={() => handleProductTypeFilter(productType)}
							type="button"
						>
							{productType.charAt(0).toUpperCase() + productType.slice(1)}
						</button>
					{/each}
				</div>
			</div>
			{@const expectationTableData = getExpectationTableData()}
			{#if expectationTableData.data.length > 0}
				<DataTable 
					headers={expectationTableData.headers}
					data={expectationTableData.data}
					maxHeight="500px"
					onRowClick={handleRowClick}
				/>
			{:else}
				<div class="no-data-message">
					<p>No expectation failures found{selectedRegionFilter ? ` for ${selectedRegionFilter}` : ''}</p>
				</div>
			{/if}
		{:else}
			<div class="no-data-message">
				<p>No expectation failures by region found</p>
			</div>
		{/if}
	</ChartCard>
</div>

<ExpectationFailureModal 
	open={showExpectationFailureModal}
	data={selectedExpectationFailure}
	onClose={closeExpectationFailureModal}
/>

<style>
	.section-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}

	.section-grid > :nth-child(3),
	.section-grid > :nth-child(4) {
		grid-column: 1 / -1;
	}

	.table-filters {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 1.5rem;
		margin-bottom: 1rem;
		padding: 0.875rem 1rem;
		background-color: #111827;
		border-radius: 0.5rem;
		border: 1px solid rgba(52, 211, 153, 0.08);
		flex-wrap: wrap;
	}

	.filter-group {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.filter-label {
		font-size: 0.8125rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-right: 0.25rem;
		white-space: nowrap;
		min-width: fit-content;
	}

	.filter-button {
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #9ca3af;
		padding: 0.2rem 0.5rem;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		white-space: nowrap;
		height: 1.75rem;
		box-sizing: border-box;
	}

	.filter-button:hover:not(.active) {
		background-color: #374151;
		color: #e5e7eb;
		border-color: var(--color-primary-dark);
	}

	.filter-button.active {
		background-color: var(--color-primary-dark);
		color: #ffffff;
		border-color: var(--color-primary-light);
		box-shadow: 0 0 0 1px var(--color-primary-light);
	}

	.no-data-message {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100px;
		color: #6b7280;
		font-size: 0.6875rem;
		background: rgba(55, 65, 81, 0.3);
		border-radius: 0.25rem;
		border: 1px dashed #374151;
	}

	@media (max-width: 768px) {
		.section-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

