<script lang="ts">
	import StackedBarChart from '../StackedBarChart.svelte';
	import ProductHeatmapChart from '../ProductHeatmapChart.svelte';
	import ChartCard from '../ChartCard.svelte';
	import type { GlobalViewData, HeatmapData } from '$lib/services/api';

	interface Props {
		globalViewData: GlobalViewData[];
		heatmapData: HeatmapData[];
		days?: number;
	}

	let { globalViewData, heatmapData, days = 7 }: Props = $props();
</script>

<div class="section-grid">
	<ChartCard title="Pass vs Fail by Region" stats={[
		{ label: 'Total Regions', value: globalViewData.length }
	]}>
		{#if globalViewData.length > 0}
			<StackedBarChart data={globalViewData} height="300px" />
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
</div>

<style>
	.section-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
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

