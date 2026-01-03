<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	interface Props {
		data: Array<{
			Region: string;
			TotalRuns: number;
			SuccessfulRuns: number;
			FailedRuns: number;
			SuccessRate: number;
		}>;
		height?: string;
	}

	let { data, height = '300px' }: Props = $props();

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

		chartInstance = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: data.map(d => d.Region),
				datasets: [
					{
						label: 'Passed',
						data: data.map(d => d.SuccessfulRuns),
						backgroundColor: '#34d399',
						borderColor: '#065f46',
						borderWidth: 1
					},
					{
						label: 'Failed',
						data: data.map(d => d.FailedRuns),
						backgroundColor: '#f87171',
						borderColor: '#991b1b',
						borderWidth: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'top',
						labels: {
							color: '#e5e7eb',
							font: { size: 14 }
						}
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
								const rawRate = data[index].SuccessRate;
								const successRate = typeof rawRate === 'number' && !isNaN(rawRate) 
									? rawRate 
									: typeof rawRate === 'string' 
										? parseFloat(rawRate) || 0 
										: 0;
								return `Success Rate: ${successRate.toFixed(1)}%`;
							}
						}
					}
				},
				scales: {
					x: {
						stacked: true,
						ticks: { 
							color: '#e5e7eb',
							font: { size: 12 }
						},
						grid: { color: 'rgba(55, 65, 81, 0.3)' }
					},
					y: {
						stacked: true,
						ticks: { 
							color: '#e5e7eb',
							font: { size: 12 }
						},
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



