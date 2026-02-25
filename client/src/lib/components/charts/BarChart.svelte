<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	interface Props {
		data: Array<{
			RuleName: string;
			TotalRuns: number;
			FailureCount: number;
			FailureRate: number;
		}>;
		height?: string;
	}

	let { data, height = '400px' }: Props = $props();

	let canvasRef: HTMLCanvasElement | null = $state(null);
	let chartInstance: Chart<'bar'> | null = $state(null);

	function createChart() {
		if (!canvasRef || !data || data.length === 0) return;

		if (chartInstance) {
			chartInstance.destroy();
			chartInstance = null;
		}

		const ctx = canvasRef.getContext('2d');
		if (!ctx) return;

		// Sort by failure count descending
		const sortedData = [...data].sort((a, b) => b.FailureCount - a.FailureCount);

		chartInstance = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: sortedData.map(d => d.RuleName),
				datasets: [
					{
						label: 'Failures',
						data: sortedData.map(d => d.FailureCount),
						backgroundColor: '#f87171',
						borderColor: '#991b1b',
						borderWidth: 1
					}
				]
			},
			options: {
				indexAxis: 'y',
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: false
					},
					tooltip: {
						backgroundColor: 'rgba(31, 41, 55, 0.95)',
						borderColor: '#10b981',
						borderWidth: 1,
						titleColor: '#e5e7eb',
						bodyColor: '#e5e7eb',
						callbacks: {
							afterLabel: function (context: any) {
								const index = context.dataIndex;
								const item = sortedData[index];
								const rawRate = item.FailureRate;
								const failureRate = typeof rawRate === 'number' && !isNaN(rawRate) 
									? rawRate 
									: typeof rawRate === 'string' 
										? parseFloat(rawRate) || 0 
										: 0;
								return [
									`Total Runs: ${item.TotalRuns}`,
									`Failure Rate: ${failureRate.toFixed(1)}%`
								];
							}
						}
					}
				},
				scales: {
					x: {
						ticks: { color: '#e5e7eb' },
						grid: { color: 'rgba(55, 65, 81, 0.3)' }
					},
					y: {
						ticks: { color: '#e5e7eb' },
						grid: { color: 'rgba(55, 65, 81, 0.3)' }
					}
				}
			}
		});
	}

	$effect(() => {
		if (canvasRef && data) {
			setTimeout(() => createChart(), 10);
		}
	});

	onDestroy(() => {
		if (chartInstance) {
			chartInstance.destroy();
			chartInstance = null;
		}
	});
</script>

<div class="chart-container" style="height: {height}">
	{#if data && data.length > 0}
		<canvas bind:this={canvasRef}></canvas>
	{:else}
		<div class="no-data">
			<p>No data available</p>
		</div>
	{/if}
</div>

<style>
	.chart-container {
		position: relative;
		width: 100%;
	}

	.no-data {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: #6b7280;
		font-size: 0.875rem;
	}
</style>



