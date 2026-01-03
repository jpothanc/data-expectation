<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	interface Props {
		data: Record<string, Array<{
			Date: string;
			RunId?: number;
			Exchange?: string;
			ProductType?: string;
			Success?: number;
			FailedExpectations?: number;
			TotalExpectations?: number;
			SuccessfulExpectations?: number;
			TotalRuns?: number;
			SuccessfulRuns?: number;
			FailedRuns: number;
			SuccessRate: number;
		}>>;
		height?: string;
	}

	let { data, height = '500px' }: Props = $props();

	let canvasRef: HTMLCanvasElement | null = $state(null);
	let chartInstance: Chart<'line'> | null = $state(null);

	function createChart() {
		if (!canvasRef || !data || Object.keys(data).length === 0) {
			if (chartInstance) {
				chartInstance.destroy();
				chartInstance = null;
			}
			return;
		}

		if (chartInstance) {
			try {
				chartInstance.destroy();
			} catch (e) {
				// Ignore errors
			}
			chartInstance = null;
		}

		const ctx = canvasRef.getContext('2d');
		if (!ctx) return;

		const regions = Object.keys(data).filter(region => 
			data[region] && Array.isArray(data[region]) && data[region].length > 0
		);
		
		// Color palette for regions
		const colors = [
			{ bg: 'rgba(16, 185, 129, 0.6)', border: '#10b981' }, // Emerald (primary)
			{ bg: 'rgba(52, 211, 153, 0.6)', border: '#34d399' }, // Emerald Light
			{ bg: 'rgba(251, 191, 36, 0.6)', border: '#fbbf24' }, // Yellow
			{ bg: 'rgba(239, 68, 68, 0.6)', border: '#ef4444' }, // Red
			{ bg: 'rgba(168, 85, 247, 0.6)', border: '#a855f7' }, // Purple
			{ bg: 'rgba(236, 72, 153, 0.6)', border: '#ec4899' }, // Pink
		];

		// Collect all unique dates
		const allDates = new Set<string>();
		regions.forEach(region => {
			const regionData = data[region];
			if (Array.isArray(regionData)) {
				regionData.forEach(run => {
					if (run && run.Date) {
						allDates.add(run.Date);
					}
				});
			}
		});
		const sortedDates = Array.from(allDates).sort((a, b) => 
			new Date(a).getTime() - new Date(b).getTime()
		);

		// Create datasets for stacked area chart
		const datasets = regions.map((region, index) => {
			const regionDataArray = data[region];
			if (!Array.isArray(regionDataArray) || regionDataArray.length === 0) {
				return null;
			}
			
			const regionData = [...regionDataArray].sort((a, b) => {
				if (!a || !b || !a.Date || !b.Date) return 0;
				const dateA = new Date(a.Date).getTime();
				const dateB = new Date(b.Date).getTime();
				return dateA - dateB;
			});

			const dataPoints = sortedDates.map((date, dateIndex) => {
				const run = regionData.find(r => r.Date === date);
				let failureCount = 0;
				if (run) {
					if (run.FailedExpectations !== undefined && run.FailedExpectations !== null) {
						failureCount = typeof run.FailedExpectations === 'number' && !isNaN(run.FailedExpectations)
							? run.FailedExpectations
							: typeof run.FailedExpectations === 'string'
								? parseInt(run.FailedExpectations) || 0
								: 0;
					} else {
						failureCount = typeof run.FailedRuns === 'number' && !isNaN(run.FailedRuns)
							? run.FailedRuns
							: typeof run.FailedRuns === 'string'
								? parseInt(run.FailedRuns) || 0
								: 0;
					}
				}
				
				return {
					x: dateIndex,
					y: failureCount,
					runData: run
				};
			});

			const color = colors[index % colors.length];

			return {
				label: region,
				data: dataPoints,
				borderColor: color.border,
				backgroundColor: color.bg,
				borderWidth: 2,
				fill: true, // Fill for area chart
				tension: 0.4,
				pointRadius: 0, // Hide points for cleaner look
				pointHoverRadius: 6,
				spanGaps: false
			};
		}).filter(dataset => dataset !== null);

		if (datasets.length === 0) {
			return;
		}

		chartInstance = new Chart(ctx, {
			type: 'line',
			data: {
				datasets: datasets
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: {
					mode: 'index',
					intersect: false
				},
				plugins: {
					legend: {
						position: 'top',
						labels: {
							color: '#e5e7eb',
							font: { size: 12 },
							usePointStyle: true,
							padding: 15
						}
					},
					tooltip: {
						backgroundColor: 'rgba(31, 41, 55, 0.95)',
						borderColor: '#10b981',
						borderWidth: 1,
						titleColor: '#e5e7eb',
						bodyColor: '#e5e7eb',
						displayColors: true,
						callbacks: {
							title: function(context: any[]) {
								if (context.length > 0 && context[0].dataIndex !== undefined) {
									const dateIndex = context[0].dataIndex;
									const date = sortedDates[dateIndex];
									if (date) {
										const d = new Date(date);
										return d.toLocaleString('en-US', { 
											month: 'short', 
											day: 'numeric', 
											year: 'numeric',
											hour: '2-digit',
											minute: '2-digit'
										});
									}
								}
								return '';
							},
							label: function (context: any) {
								const region = context.dataset.label;
								const failureCount = context.parsed.y;
								return `${region}: ${failureCount} ${failureCount === 1 ? 'failure' : 'failures'}`;
							},
							footer: function(tooltipItems: any[]) {
								const total = tooltipItems.reduce((sum, item) => sum + item.parsed.y, 0);
								return `Total: ${total} ${total === 1 ? 'failure' : 'failures'}`;
							}
						}
					}
				},
				scales: {
					x: {
						type: 'category',
						position: 'bottom',
						labels: sortedDates.map(date => {
							const d = new Date(date);
							return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
						}),
						stacked: true,
						grid: {
							color: 'rgba(55, 65, 81, 0.3)',
							drawBorder: false
						},
						ticks: {
							color: '#9ca3af',
							font: { size: 11 },
							maxRotation: 45,
							minRotation: 0,
							maxTicksLimit: 12
						},
						title: {
							display: true,
							text: 'Date',
							color: '#9ca3af',
							font: { size: 12 }
						}
					},
					y: {
						stacked: true,
						beginAtZero: true,
						grid: {
							color: 'rgba(55, 65, 81, 0.3)',
							drawBorder: false
						},
						ticks: {
							color: '#9ca3af',
							font: { size: 11 },
							callback: function (value: any) {
								return Number.isInteger(value) ? value : Math.round(value);
							}
						},
						title: {
							display: true,
							text: 'Failed Expectations (Stacked)',
							color: '#9ca3af',
							font: { size: 12 }
						}
					}
				}
			}
		});
	}

	let isUpdating = $state(false);
	let lastDataHash = $state<string>('');
	
	$effect(() => {
		if (isUpdating) return;
		
		const dataHash = data && Object.keys(data).length > 0 
			? Object.keys(data).sort().map(region => {
				const points = data[region];
				return `${region}:${points.length}-${points.map(d => d.Date).join(',')}`;
			}).join('|')
			: '';
		
		const hasData = data && Object.keys(data).length > 0;
		if (canvasRef && hasData) {
			if (dataHash !== lastDataHash || !chartInstance) {
				isUpdating = true;
				lastDataHash = dataHash;
				try {
					createChart();
				} catch (err) {
					console.error('Error creating chart:', err);
				} finally {
					setTimeout(() => {
						isUpdating = false;
					}, 0);
				}
			}
		} else if (chartInstance) {
			try {
				chartInstance.destroy();
				chartInstance = null;
			} catch (e) {
				console.warn('Error destroying chart:', e);
			}
			lastDataHash = '';
		}
	});

	onDestroy(() => {
		if (chartInstance) {
			chartInstance.destroy();
		}
	});
</script>

<div class="chart-container" style="height: {height};">
	{#if !data || Object.keys(data).length === 0}
		<div class="no-data">
			<p>No trend data available</p>
		</div>
	{:else}
		<canvas bind:this={canvasRef}></canvas>
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
		background: rgba(55, 65, 81, 0.3);
		border-radius: 0.5rem;
		border: 1px dashed #374151;
	}
</style>

