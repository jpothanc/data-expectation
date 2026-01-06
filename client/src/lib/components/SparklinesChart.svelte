<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { RegionalTrendResponse } from '../services/api';

	interface Props {
		data: RegionalTrendResponse['data'];
		height?: string;
	}

	let { data, height = '500px' }: Props = $props();

	function getFailureCount(run: any): number {
		if (run.FailedExpectations !== undefined && run.FailedExpectations !== null) {
			return typeof run.FailedExpectations === 'number' && !isNaN(run.FailedExpectations)
				? run.FailedExpectations
				: typeof run.FailedExpectations === 'string'
					? parseInt(run.FailedExpectations) || 0
					: 0;
		}
		return typeof run.FailedRuns === 'number' && !isNaN(run.FailedRuns)
			? run.FailedRuns
			: typeof run.FailedRuns === 'string'
				? parseInt(run.FailedRuns) || 0
				: 0;
	}

	function getSuccessRate(run: any): number {
		return typeof run.SuccessRate === 'number' 
			? run.SuccessRate 
			: parseFloat(String(run.SuccessRate)) || 0;
	}

	const regions = $derived.by(() => {
		if (!data || typeof data !== 'object') return [];
		return Object.keys(data).filter(region => {
			const regionData = data[region];
			return regionData && Array.isArray(regionData) && regionData.length > 0;
		});
	});
	
	function getSparklineData(region: string) {
		if (!data || !data[region]) {
			return {
				path: '',
				failures: [],
				successRates: [],
				totalFailures: 0,
				avgSuccessRate: 0,
				trend: 0
			};
		}

		const regionDataArray = data[region];
		if (!Array.isArray(regionDataArray) || regionDataArray.length === 0) {
			return {
				path: '',
				failures: [],
				successRates: [],
				totalFailures: 0,
				avgSuccessRate: 0,
				trend: 0
			};
		}
		
		const regionData = [...regionDataArray].sort((a, b) => {
			if (!a || !b || !a.Date || !b.Date) return 0;
			return new Date(a.Date).getTime() - new Date(b.Date).getTime();
		});
		
		const failures = regionData.map(run => getFailureCount(run));
		const successRates = regionData.map(run => getSuccessRate(run));
		
		const maxFailure = Math.max(...failures, 1);
		const minFailure = Math.min(...failures);
		const range = maxFailure - minFailure || 1;
		
		// Normalize to 0-100 for SVG
		const normalizedFailures = failures.map(f => 
			range > 0 ? ((f - minFailure) / range) * 100 : 50
		);
		
		// Generate SVG path
		const width = 200;
		const height = 40;
		const stepX = width / (normalizedFailures.length - 1 || 1);
		
		let path = '';
		normalizedFailures.forEach((value, index) => {
			const x = index * stepX;
			const y = height - (value / 100) * height;
			if (index === 0) {
				path += `M ${x} ${y}`;
			} else {
				path += ` L ${x} ${y}`;
			}
		});
		
		return {
			path,
			failures,
			successRates,
			totalFailures: failures.reduce((sum, f) => sum + f, 0),
			avgSuccessRate: successRates.reduce((sum, r) => sum + r, 0) / successRates.length || 0,
			trend: failures.length > 1 
				? (failures[failures.length - 1] - failures[0]) / failures.length
				: 0
		};
	}
</script>

<div class="sparklines-container" style="height: {height};">
	{#if regions.length === 0}
		<div class="no-data">
			<p>No trend data available</p>
		</div>
	{:else}
		<div class="sparklines-grid">
			{#each regions as region}
				{@const sparkData = getSparklineData(region)}
				<div class="sparkline-card">
					<div class="sparkline-header">
						<h3 class="region-name">{region}</h3>
						<div class="sparkline-stats">
							<span class="stat-badge failures">
								{sparkData.totalFailures} {sparkData.totalFailures === 1 ? 'failure' : 'failures'}
							</span>
							<span class="stat-badge success-rate">
								{sparkData.avgSuccessRate.toFixed(1)}% success
							</span>
						</div>
					</div>
					<div class="sparkline-chart">
						<svg viewBox="0 0 200 40" class="sparkline-svg">
							<path 
								d={sparkData.path} 
								fill="none" 
								stroke={sparkData.trend >= 0 ? '#ef4444' : '#10b981'}
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
							<!-- Fill area -->
							<path 
								d="{sparkData.path} L 200 40 L 0 40 Z" 
								fill={sparkData.trend >= 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)'}
							/>
						</svg>
					</div>
					<div class="sparkline-footer">
						<span class="trend-indicator {sparkData.trend >= 0 ? 'trending-up' : 'trending-down'}">
							{#if sparkData.trend >= 0}
								<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
								</svg>
								Trending up
							{:else}
								<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
								</svg>
								Trending down
							{/if}
						</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.sparklines-container {
		position: relative;
		width: 100%;
		overflow-y: auto;
	}

	/* Custom scrollbar styling with theme */
	.sparklines-container::-webkit-scrollbar {
		width: 10px;
	}

	.sparklines-container::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 5px;
	}

	.sparklines-container::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.sparklines-container::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	/* Firefox scrollbar */
	.sparklines-container {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.sparklines-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}

	.sparkline-card {
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		padding: 1rem;
		transition: border-color 0.2s, box-shadow 0.2s;
	}

	.sparkline-card:hover {
		border-color: #34d399;
		box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
	}

	.sparkline-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.75rem;
		gap: 0.5rem;
	}

	.region-name {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #e5e7eb;
	}

	.sparkline-stats {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		align-items: flex-end;
	}

	.stat-badge {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-weight: 500;
	}

	.stat-badge.failures {
		background-color: rgba(239, 68, 68, 0.2);
		color: #fca5a5;
	}

	.stat-badge.success-rate {
		background-color: rgba(16, 185, 129, 0.2);
		color: #6ee7b7;
	}

	.sparkline-chart {
		margin: 0.5rem 0;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.sparkline-svg {
		width: 100%;
		height: 100%;
	}

	.sparkline-footer {
		display: flex;
		justify-content: center;
		margin-top: 0.5rem;
		padding-top: 0.5rem;
		border-top: 1px solid #374151;
	}

	.trend-indicator {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.trend-indicator svg {
		width: 1rem;
		height: 1rem;
	}

	.trend-indicator.trending-up {
		color: #ef4444;
	}

	.trend-indicator.trending-down {
		color: #10b981;
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

