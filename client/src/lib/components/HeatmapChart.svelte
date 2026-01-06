<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { RegionalTrendResponse, ExchangeValidationResponse } from '../services/api';
	import { getValidationResultsByRegionDate } from '../services/api';
	import { withTimeout } from '../utils/promise';
	import { API_TIMEOUTS } from '../constants/timeouts';
	import ErrorDetailsPanel from './ErrorDetailsPanel.svelte';

	interface Props {
		data: RegionalTrendResponse['data'];
		height?: string;
		days?: number;
	}

	let { data, height = '900px', days = 30 }: Props = $props();

	let selectedRegion = $state<string | null>(null);
	let selectedDate = $state<string | null>(null);
	let errorDetails = $state<ExchangeValidationResponse | null>(null);
	let loadingDetails = $state(false);
	let errorDetailsError = $state<string | null>(null);
	let showErrorModal = $state(false);

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

	function getColorIntensity(value: number, maxValue: number): string {
		if (maxValue === 0) return 'rgba(55, 65, 81, 0.3)';
		const intensity = value / maxValue;
		
		// Color scale: green (low) -> yellow -> orange -> red (high)
		if (intensity < 0.2) {
			// Green (low failures)
			const alpha = 0.3 + (intensity * 0.5);
			return `rgba(16, 185, 129, ${alpha})`;
		} else if (intensity < 0.5) {
			// Yellow
			const alpha = 0.4 + ((intensity - 0.2) * 0.6);
			return `rgba(251, 191, 36, ${alpha})`;
		} else if (intensity < 0.8) {
			// Orange
			const alpha = 0.5 + ((intensity - 0.5) * 0.5);
			return `rgba(249, 115, 22, ${alpha})`;
		} else {
			// Red (high failures)
			const alpha = 0.6 + ((intensity - 0.8) * 0.4);
			return `rgba(239, 68, 68, ${alpha})`;
		}
	}

	// Process data for heatmap reactively
	const processedData = $derived.by(() => {
		if (!data || typeof data !== 'object') {
			return {
				regions: [],
				sortedDates: [],
				heatmapData: {} as Record<string, Record<string, number>>,
				maxValue: 0
			};
		}

		const regions = Object.keys(data).filter(region => {
			const regionData = data[region];
			return regionData && Array.isArray(regionData) && regionData.length > 0;
		});

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

		// Create heatmap matrix: [region][date] = failureCount
		const heatmapData: Record<string, Record<string, number>> = {};
		let maxValue = 0;

		regions.forEach(region => {
			const regionData = data[region];
			if (!Array.isArray(regionData)) return;
			
			heatmapData[region] = {};
			sortedDates.forEach(date => {
				const run = regionData.find(r => r && r.Date === date);
				const count = run ? getFailureCount(run) : 0;
				heatmapData[region][date] = count;
				maxValue = Math.max(maxValue, count);
			});
		});

		return { regions, sortedDates, heatmapData, maxValue };
	});

	const { regions, sortedDates, heatmapData, maxValue } = processedData;

	function formatDate(dateStr: string): string {
		const d = new Date(dateStr);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function formatDateWithTime(dateStr: string): string {
		const d = new Date(dateStr);
		const datePart = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
		const timePart = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
		return `${datePart}\n${timePart}`;
	}

	function formatDateTime(dateStr: string): string {
		const d = new Date(dateStr);
		return d.toLocaleString('en-US', { 
			month: 'short', 
			day: 'numeric', 
			hour: '2-digit', 
			minute: '2-digit' 
		});
	}

	function parseDateForAPI(dateStr: string): string {
		// Convert date string to YYYY-MM-DD format for API
		const d = new Date(dateStr);
		return d.toISOString().split('T')[0];
	}

	async function handleCellClick(region: string, date: string) {
		const count = heatmapData[region]?.[date] || 0;
		
		// Only show error details if there are failures
		if (count > 0) {
			selectedRegion = region;
			selectedDate = date;
			await fetchErrorDetails(region, date);
		}
	}

	async function fetchErrorDetails(region: string, date: string) {
		loadingDetails = true;
		errorDetailsError = null;
		showErrorModal = true;

		try {
			const dateFormatted = parseDateForAPI(date);
			const result = await withTimeout(
				getValidationResultsByRegionDate(region, dateFormatted, days, 200),
				API_TIMEOUTS.STANDARD
			);
			
			if (result.runs.length > 0) {
				errorDetails = result;
			} else {
				errorDetailsError = 'No error details found for this region and date combination';
			}
		} catch (err) {
			console.error('Error fetching error details:', err);
			errorDetailsError = err instanceof Error ? err.message : 'Failed to fetch error details';
		} finally {
			loadingDetails = false;
		}
	}

	function closeErrorModal() {
		showErrorModal = false;
		errorDetails = null;
		selectedRegion = null;
		selectedDate = null;
		errorDetailsError = null;
	}
</script>

<div class="heatmap-container" style="height: {height};">
	{#if regions.length === 0 || sortedDates.length === 0}
		<div class="no-data">
			<p>No trend data available</p>
		</div>
	{:else}
		<div class="heatmap-wrapper">
			<div class="heatmap-header">
				<div class="date-labels">
					{#each sortedDates as date}
						<div class="date-label" title={formatDateTime(date)}>
							<span class="date-part">{formatDate(date)}</span>
							<span class="time-part">{new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}</span>
						</div>
					{/each}
				</div>
			</div>
			<div class="heatmap-body">
				{#each regions as region}
					<div class="heatmap-row">
						<div class="region-label">{region}</div>
						<div class="heatmap-cells">
							{#each sortedDates as date}
								{@const count = heatmapData[region][date] || 0}
								{@const color = getColorIntensity(count, maxValue)}
								<div 
									class="heatmap-cell {count > 0 ? 'clickable' : ''}"
									style="background-color: {color};"
									title="{region} - {formatDate(date)}: {count} {count === 1 ? 'failure' : 'failures'}"
									onclick={() => count > 0 && handleCellClick(region, date)}
									role={count > 0 ? 'button' : undefined}
									tabindex={count > 0 ? 0 : undefined}
									onkeydown={(e) => {
										if (count > 0 && (e.key === 'Enter' || e.key === ' ')) {
											e.preventDefault();
											handleCellClick(region, date);
										}
									}}
								>
									<span class="cell-value">{count > 0 ? count : ''}</span>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
			<div class="heatmap-legend">
				<span class="legend-label">Low</span>
				<div class="legend-gradient"></div>
				<span class="legend-label">High</span>
			</div>
		</div>
	{/if}
</div>

{#if showErrorModal}
	{@const formattedDate = selectedDate ? formatDate(selectedDate) : ''}
	<ErrorDetailsPanel
		isOpen={showErrorModal}
		title={selectedRegion && formattedDate ? `${selectedRegion} - ${formattedDate}` : 'Error Details'}
		results={errorDetails?.runs || []}
		loading={loadingDetails}
		error={errorDetailsError}
		onClose={closeErrorModal}
	/>
{/if}


<style>
	.heatmap-container {
		position: relative;
		width: 100%;
		overflow-x: auto;
		overflow-y: visible;
		/* Firefox scrollbar */
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	/* Custom scrollbar styling with theme */
	.heatmap-container::-webkit-scrollbar {
		height: 10px !important;
	}

	.heatmap-container::-webkit-scrollbar-track {
		background: #111827 !important;
		border-radius: 5px;
	}

	.heatmap-container::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark) !important;
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.heatmap-container::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary) !important;
	}

	.heatmap-wrapper {
		min-width: 100%;
	}

	.heatmap-header {
		margin-bottom: 0.5rem;
	}

	.date-labels {
		display: flex;
		gap: 2px;
		margin-left: 160px; /* Match region label width */
		padding-left: 0.75rem;
	}

	.date-label {
		font-size: 0.875rem;
		color: #9ca3af;
		writing-mode: vertical-rl;
		text-orientation: mixed;
		min-width: 30px;
		text-align: center;
		padding: 0.5rem 0;
	}

	.heatmap-body {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.heatmap-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.region-label {
		width: 160px;
		font-size: 1.0625rem;
		color: #e5e7eb;
		font-weight: 500;
		text-align: right;
		padding-right: 1.25rem;
		flex-shrink: 0;
	}

	.heatmap-cells {
		display: flex;
		gap: 2px;
		flex: 1;
	}

	.heatmap-cell {
		min-width: 40px;
		height: 60px;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: transform 0.1s, box-shadow 0.1s;
		border: 1px solid rgba(55, 65, 81, 0.5);
	}

	.heatmap-cell.clickable {
		cursor: pointer;
	}

	.heatmap-cell.clickable:hover {
		transform: scale(1.1);
		box-shadow: 0 0 8px var(--shadow-strong);
		z-index: 10;
		position: relative;
	}

	.heatmap-cell.clickable:focus {
		outline: 2px solid var(--color-primary-light);
		outline-offset: 2px;
	}

	.cell-value {
		font-size: 0.875rem;
		color: #ffffff;
		font-weight: 600;
		text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
	}

	.heatmap-legend {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 1.5rem;
		margin-left: 160px;
		padding-left: 0.75rem;
	}

	.legend-label {
		font-size: 0.875rem;
		color: #9ca3af;
		font-weight: 500;
	}

	.legend-gradient {
		width: 300px;
		height: 30px;
		background: linear-gradient(to right, 
			rgba(16, 185, 129, 0.3),
			rgba(251, 191, 36, 0.5),
			rgba(249, 115, 22, 0.7),
			rgba(239, 68, 68, 0.9)
		);
		border-radius: 6px;
		border: 1px solid rgba(55, 65, 81, 0.5);
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
