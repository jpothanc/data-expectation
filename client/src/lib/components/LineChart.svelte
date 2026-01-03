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
		chartType?: 'line' | 'area';
		showSuccessRate?: boolean;
	}

	let { data, height = '300px', chartType = 'line', showSuccessRate = false }: Props = $props();

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

		// Destroy existing chart before creating new one
		if (chartInstance) {
			try {
				chartInstance.destroy();
			} catch (e) {
				// Ignore errors when destroying chart
			}
			chartInstance = null;
		}

		const ctx = canvasRef.getContext('2d');
		if (!ctx) return;

		// Get regions from data keys (already grouped by region)
		const regions = Object.keys(data).filter(region => {
			// Ensure region has valid data array
			return data[region] && Array.isArray(data[region]) && data[region].length > 0;
		});
		
		// Debug: Log regions found
		console.log('[LineChart] Regions found:', regions);
		console.log('[LineChart] Data keys:', Object.keys(data));
		regions.forEach(region => {
			console.log(`[LineChart] ${region}: ${data[region].length} data points`);
		});
		
		// Color palette for regions - deterministic mapping by region name
		const regionColorMap: Record<string, { bg: string; border: string }> = {
			'APAC': { bg: 'rgba(16, 185, 129, 0.2)', border: '#10b981' }, // Emerald (primary)
			'EMEA': { bg: 'rgba(251, 191, 36, 0.2)', border: '#fbbf24' }, // Yellow
			'US': { bg: 'rgba(239, 68, 68, 0.2)', border: '#ef4444' }, // Red
			'AMERICAS': { bg: 'rgba(168, 85, 247, 0.2)', border: '#a855f7' }, // Purple
			'ASIA': { bg: 'rgba(236, 72, 153, 0.2)', border: '#ec4899' }, // Pink
			'EUROPE': { bg: 'rgba(52, 211, 153, 0.2)', border: '#34d399' }, // Emerald Light
		};
		
		// Fallback colors for unknown regions
		const fallbackColors = [
			{ bg: 'rgba(16, 185, 129, 0.2)', border: '#10b981' }, // Emerald
			{ bg: 'rgba(52, 211, 153, 0.2)', border: '#34d399' }, // Emerald Light
			{ bg: 'rgba(251, 191, 36, 0.2)', border: '#fbbf24' }, // Yellow
			{ bg: 'rgba(239, 68, 68, 0.2)', border: '#ef4444' }, // Red
			{ bg: 'rgba(168, 85, 247, 0.2)', border: '#a855f7' }, // Purple
			{ bg: 'rgba(236, 72, 153, 0.2)', border: '#ec4899' }, // Pink
		];
		
		// Function to get color for a region (deterministic)
		function getRegionColor(region: string, index: number): { bg: string; border: string } {
			const normalizedRegion = region.toUpperCase();
			return regionColorMap[normalizedRegion] || fallbackColors[index % fallbackColors.length];
		}
		
		// Collect all unique dates across all regions for proper time scale
		const allDates = new Set<string>();
		regions.forEach(region => {
			if (data[region] && Array.isArray(data[region])) {
				data[region].forEach(run => {
					if (run && run.Date) {
						allDates.add(run.Date);
					}
				});
			}
		});
		const sortedDates = Array.from(allDates).sort((a, b) => 
			new Date(a).getTime() - new Date(b).getTime()
		);
		
		// Create datasets for each region - data is already grouped by region
		const datasets = regions.map((region, index) => {
			// Ensure we have valid data for this region
			if (!data[region] || !Array.isArray(data[region]) || data[region].length === 0) {
				console.warn(`[LineChart] Skipping region ${region}: invalid or empty data`);
				return null;
			}
			
			// Data is already sorted by backend, but ensure it's sorted by date
			const regionData = [...data[region]].filter(run => run && run.Date).sort((a, b) => {
				const dateA = new Date(a.Date).getTime();
				const dateB = new Date(b.Date).getTime();
				return dateA - dateB;
			});
			
			if (regionData.length === 0) {
				console.warn(`[LineChart] Skipping region ${region}: no valid data points after filtering`);
				return null;
			}
			
			// Create data points with x (date index) and y (failure count) for each run
			const dataPoints = regionData.map((run) => {
				// Prefer FailedExpectations if available, otherwise use FailedRuns
				let failureCount = 0;
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
				
				// Find index of this date in sortedDates array
				const dateIndex = sortedDates.indexOf(run.Date);
				
				return {
					x: dateIndex >= 0 ? dateIndex : sortedDates.length, // X-axis: date index
					y: failureCount, // Y-axis: failure count
					runData: run // Store full run data for tooltip
				};
			});

			const color = getRegionColor(region, index);

			return {
				label: region,
				data: dataPoints,
				borderColor: color.border,
				backgroundColor: chartType === 'area' ? color.bg : 'transparent',
				borderWidth: 2,
				fill: chartType === 'area', // Fill under line for area chart
				tension: 0.4,
				pointRadius: 4,
				pointHoverRadius: 6,
				pointBackgroundColor: color.border,
				pointBorderColor: '#1f2937',
				pointBorderWidth: 2,
				spanGaps: false // Don't connect points across gaps
			};
		}).filter(dataset => dataset !== null); // Remove null datasets

		// Add success rate dataset if requested
		if (showSuccessRate) {
			regions.forEach((region, index) => {
				const regionData = [...data[region]].sort((a, b) => {
					const dateA = new Date(a.Date).getTime();
					const dateB = new Date(b.Date).getTime();
					return dateA - dateB;
				});

				const successRatePoints = regionData.map((run) => {
					const successRate = typeof run.SuccessRate === 'number' 
						? run.SuccessRate 
						: parseFloat(String(run.SuccessRate)) || 0;
					
					// Find index of this date in sortedDates array
					const dateIndex = sortedDates.indexOf(run.Date);
					
					return {
						x: dateIndex >= 0 ? dateIndex : sortedDates.length,
						y: successRate,
						runData: run
					};
				});

				const color = getRegionColor(region, index);
				datasets.push({
					label: `${region} - Success Rate`,
					data: successRatePoints,
					borderColor: color.border,
					backgroundColor: 'transparent',
					borderWidth: 2,
					borderDash: [5, 5], // Dashed line for success rate
					fill: false,
					tension: 0.4,
					pointRadius: 3,
					pointHoverRadius: 5,
					pointBackgroundColor: color.border,
					pointBorderColor: '#1f2937',
					pointBorderWidth: 1,
					yAxisID: 'y1', // Use secondary y-axis
					spanGaps: false
				});
			});
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
					mode: 'point',
					intersect: true,
					axis: 'xy'
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
						filter: function(tooltipItem: any) {
							// Only show tooltip for the exact point being hovered
							// This ensures only one entry shows at a time
							return true;
						},
						callbacks: {
							title: function(context: any[]) {
								// Show the date/time for the hovered point
								if (context.length > 0 && context[0].raw?.runData) {
									const date = new Date(context[0].raw.runData.Date);
									return date.toLocaleString('en-US', { 
										month: 'short', 
										day: 'numeric', 
										year: 'numeric',
										hour: '2-digit',
										minute: '2-digit'
									});
								}
								return '';
							},
							label: function (context: any) {
								const region = context.dataset.label;
								const failureCount = context.parsed.y;
								
								// Get the run data stored in the data point
								const runData = context.raw?.runData;
								
								if (!runData) return `${region}: ${failureCount} ${failureCount === 1 ? 'failure' : 'failures'}`;
								
								const successRate = typeof runData.SuccessRate === 'number' 
									? runData.SuccessRate 
									: parseFloat(runData.SuccessRate) || 0;
								
								const tooltipLines = [
									`${region}: ${failureCount} ${failureCount === 1 ? 'failure' : 'failures'}`
								];
								
								if (runData.Exchange) {
									tooltipLines.push(`Exchange: ${runData.Exchange}`);
								}
								
								if (runData.TotalExpectations !== undefined && runData.TotalExpectations !== null) {
									tooltipLines.push(`Expectations: ${runData.SuccessfulExpectations || 0}/${runData.TotalExpectations} passed`);
								}
								
								tooltipLines.push(`Success Rate: ${successRate.toFixed(1)}%`);
								
								if (runData.RunId) {
									tooltipLines.push(`Run ID: ${runData.RunId}`);
								}
								
								return tooltipLines;
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
						grid: {
							color: 'rgba(55, 65, 81, 0.3)',
							drawBorder: false
						},
						ticks: {
							color: '#9ca3af',
							font: { size: 11 },
							maxRotation: 45,
							minRotation: 0,
							maxTicksLimit: 12 // Limit number of ticks for readability
						},
						title: {
							display: true,
							text: 'Date',
							color: '#9ca3af',
							font: { size: 12 }
						}
					},
					y: {
						id: 'y',
						beginAtZero: true,
						position: 'left',
						grid: {
							color: 'rgba(55, 65, 81, 0.3)',
							drawBorder: false
						},
						ticks: {
							color: '#9ca3af',
							font: { size: 11 },
							callback: function (value: any) {
								// Show as integer count
								return Number.isInteger(value) ? value : Math.round(value);
							}
						},
						title: {
							display: true,
							text: 'Failed Expectations',
							color: '#9ca3af',
							font: { size: 12 }
						}
					},
					...(showSuccessRate ? {
						y1: {
							id: 'y1',
							type: 'linear',
							position: 'right',
							beginAtZero: true,
							max: 100,
							grid: {
								drawOnChartArea: false // Don't draw grid for secondary axis
							},
							ticks: {
								color: '#9ca3af',
								font: { size: 11 },
								callback: function (value: any) {
									return value + '%';
								}
							},
							title: {
								display: true,
								text: 'Success Rate (%)',
								color: '#9ca3af',
								font: { size: 12 }
							}
						}
					} : {})
				}
			}
		});
	}

	// Use a guard to prevent infinite loops from reactive updates
	let isUpdating = $state(false);
	let lastDataHash = $state<string>('');
	
	$effect(() => {
		// Prevent concurrent updates
		if (isUpdating) return;
		
		// Create a simple hash of the data to detect actual changes
		// Data is now nested by region: { "APAC": [...], "US": [...] }
		const dataHash = data && Object.keys(data).length > 0 
			? Object.keys(data).sort().map(region => {
				const points = data[region];
				return `${region}:${points.length}-${points.map(d => d.Date).join(',')}`;
			}).join('|')
			: '';
		
		// Only update if data actually changed or canvas ref changed
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
					// Use setTimeout to break reactive cycle
					setTimeout(() => {
						isUpdating = false;
					}, 0);
				}
			}
		} else if (chartInstance) {
			// Clean up if data is no longer available
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

