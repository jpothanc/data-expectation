<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	interface Props {
		data: Array<{
			Region: string;
			ColumnName: string;
			ExpectationType: string;
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

		// Group data by region
		const regions = [...new Set(data.map(d => d.Region))].sort();
		// Create labels combining ColumnName and ExpectationType
		const expectationKeys = [...new Set(data.map(d => `${d.ColumnName} - ${d.ExpectationType}`))].sort();
		
		// Create datasets for each region
		const datasets = regions.map((region, index) => {
			const colors = [
				{ bg: 'rgba(239, 68, 68, 0.8)', border: 'rgba(239, 68, 68, 1)' }, // red
				{ bg: 'rgba(59, 130, 246, 0.8)', border: 'rgba(59, 130, 246, 1)' }, // blue
				{ bg: 'rgba(16, 185, 129, 0.8)', border: 'rgba(16, 185, 129, 1)' }, // green
				{ bg: 'rgba(245, 158, 11, 0.8)', border: 'rgba(245, 158, 11, 1)' }, // yellow
				{ bg: 'rgba(168, 85, 247, 0.8)', border: 'rgba(168, 85, 247, 1)' }  // purple
			];
			const color = colors[index % colors.length];
			
			return {
				label: region,
				data: expectationKeys.map(key => {
					const [columnName, expectationType] = key.split(' - ');
					const item = data.find(d => d.Region === region && d.ColumnName === columnName && d.ExpectationType === expectationType);
					return item ? item.FailureCount : 0;
				}),
				backgroundColor: color.bg,
				borderColor: color.border,
				borderWidth: 1
			};
		});

		chartInstance = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: expectationKeys,
				datasets: datasets
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: true,
						position: 'top',
						labels: {
							color: '#e5e7eb',
							font: {
								size: 12
							}
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
								const region = datasets[context.datasetIndex].label;
								const label = expectationKeys[context.dataIndex];
								const [columnName, expectationType] = label.split(' - ');
								const item = data.find(d => d.Region === region && d.ColumnName === columnName && d.ExpectationType === expectationType);
								if (item) {
									const rawRate = item.FailureRate;
									const failureRate = typeof rawRate === 'number' && !isNaN(rawRate) 
										? rawRate 
										: typeof rawRate === 'string' 
											? parseFloat(rawRate) || 0 
											: 0;
									return [
										`Column: ${item.ColumnName}`,
										`Expectation: ${item.ExpectationType}`,
										`Total Runs: ${item.TotalRuns}`,
										`Failure Rate: ${failureRate.toFixed(1)}%`
									];
								}
								return [];
							}
						}
					}
				},
				scales: {
					x: {
						ticks: { 
							color: '#e5e7eb',
							maxRotation: 45,
							minRotation: 45,
							font: {
								size: 10
							}
						},
						grid: { color: 'rgba(55, 65, 81, 0.3)' }
					},
					y: {
						ticks: { color: '#e5e7eb' },
						grid: { color: 'rgba(55, 65, 81, 0.3)' },
						beginAtZero: true
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



