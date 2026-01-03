<script lang="ts">
	import TreemapChart from '../TreemapChart.svelte';
	import ChartCard from '../ChartCard.svelte';
	import type { TreemapData } from '$lib/services/api';

	interface Props {
		treemapData: TreemapData[];
		onExchangeClick?: (exchange: string) => void;
	}

	let { treemapData, onExchangeClick }: Props = $props();
</script>

<div class="section-grid">
	<ChartCard title="Regional Exchange Breakdown" stats={[
		{ label: 'Exchanges', value: treemapData.length }
	]}>
		{#if treemapData.length > 0}
			<TreemapChart data={treemapData} onExchangeClick={onExchangeClick} />
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

