<script lang="ts">
	import LineChart from '../charts/LineChart.svelte';
	import ChartCard from '../charts/ChartCard.svelte';
	import type { RegionalTrendResponse } from '$lib/services/api';

	interface Props {
		regionalTrendsData: RegionalTrendResponse | null;
	}

	let { regionalTrendsData }: Props = $props();
</script>

<div class="section-grid">
	<ChartCard title="Failure Trends by Region" stats={regionalTrendsData ? [
		{ label: 'Data Points', value: Object.values(regionalTrendsData.data).flat().length },
		{ label: 'Regions', value: Object.keys(regionalTrendsData.data).length },
		{ label: 'Total Failures', value: Object.values(regionalTrendsData.data).flat().reduce((sum, d) => sum + (d.FailedRuns || 0), 0) }
	] : []}>
		{#if regionalTrendsData && Object.keys(regionalTrendsData.data).length > 0}
			<LineChart data={regionalTrendsData.data} height="300px" />
		{:else}
			<div class="no-data-message">
				<p>No trend data available</p>
			</div>
		{/if}
	</ChartCard>
</div>

<style>
	.section-grid {
		display: grid;
		grid-template-columns: 1fr;
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
</style>

