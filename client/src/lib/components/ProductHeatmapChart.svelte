<script lang="ts">
	import { goto } from '$app/navigation';
	import type { HeatmapData } from '../services/api';
	import { getExchangeValidationResults, type ExchangeValidationResponse } from '../services/api';
	import { withTimeout } from '../utils/promise';
	import { API_TIMEOUTS } from '../constants/timeouts';
	import ErrorDetailsPanel from './ErrorDetailsPanel.svelte';

	interface Props {
		data: HeatmapData[];
		height?: string;
		days?: number;
	}

	let { data, height = '800px', days = 7 }: Props = $props();

	let selectedRegion = $state<string | null>(null);
	let selectedProductType = $state<string | null>(null);
	let errorDetails = $state<ExchangeValidationResponse | null>(null);
	let loadingDetails = $state(false);
	let errorDetailsError = $state<string | null>(null);
	let showErrorModal = $state(false);

	async function handleCellClick(region: string, productType: string) {
		const item = data.find(d => d.Region === region && d.ProductType === productType);
		
		// Check if there are errors (low success rate or failed runs)
		if (item && (item.SuccessRate < 100 || (item.TotalRuns - item.SuccessfulRuns) > 0)) {
			// Show error details modal
			selectedRegion = region;
			selectedProductType = productType;
			await fetchErrorDetails(region, productType);
		} else {
			// Navigate to breakdown page for cells without errors
			const params = new URLSearchParams({
				region: region,
				productType: productType
			});
			goto(`/analytics/breakdown?${params.toString()}`);
		}
	}

	async function fetchErrorDetails(region: string, productType: string) {
		loadingDetails = true;
		errorDetailsError = null;
		showErrorModal = true;

		try {
			// Get exchanges from config - common exchanges
			const exchanges = ['XHKG', 'XNSE', 'XTKS', 'XNYS'];
			
			// Fetch results from all exchanges in parallel and filter by region/product type
			const fetchPromises = exchanges.map(async (exchange) => {
				try {
					const result = await withTimeout(
						getExchangeValidationResults(exchange, days, 200), // Increased limit to get more results
						API_TIMEOUTS.STANDARD
					);
					
					// Filter results by region and product type, only failed runs
					const filteredRuns = result.runs.filter(run => 
						run.Region?.toUpperCase() === region.toUpperCase() && 
						run.ProductType?.toLowerCase() === productType.toLowerCase() &&
						!run.Success // Only show failed runs
					);
					
					return filteredRuns;
				} catch (err) {
					// Continue with next exchange if one fails
					console.warn(`Failed to fetch results for ${exchange}:`, err);
					return [];
				}
			});
			
			// Wait for all requests to complete
			const allFilteredRuns = await Promise.all(fetchPromises);
			const combinedRuns = allFilteredRuns.flat();
			
			if (combinedRuns.length > 0) {
				errorDetails = {
					exchange: `${region} - ${productType}`,
					total_runs: combinedRuns.length,
					runs: combinedRuns
				};
			} else {
				errorDetailsError = 'No error details found for this region and product type combination';
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
		selectedProductType = null;
		errorDetailsError = null;
	}

	function getColorIntensity(value: number): string {
		// SuccessRate is 0-100, color scale: red (low) -> yellow -> green (high)
		if (value >= 95) {
			// Green (excellent)
			return 'rgba(16, 185, 129, 0.8)';
		} else if (value >= 85) {
			// Light green (good)
			return 'rgba(34, 197, 94, 0.7)';
		} else if (value >= 75) {
			// Yellow (fair)
			return 'rgba(251, 191, 36, 0.6)';
		} else if (value >= 65) {
			// Orange (poor)
			return 'rgba(249, 115, 22, 0.7)';
		} else {
			// Red (very poor)
			return 'rgba(239, 68, 68, 0.8)';
		}
	}

	// Process data for heatmap
	const processedData = $derived.by(() => {
		if (!data || !Array.isArray(data) || data.length === 0) {
			return {
				regions: [],
				productTypes: [],
				heatmapData: {} as Record<string, Record<string, number>>,
				maxValue: 100,
				minValue: 0
			};
		}

		const regions = [...new Set(data.map(d => d.Region))].sort();
		const productTypes = [...new Set(data.map(d => d.ProductType))].sort();

		// Create heatmap matrix: [region][productType] = successRate
		const heatmapData: Record<string, Record<string, number>> = {};
		let maxValue = 0;
		let minValue = 100;

		regions.forEach(region => {
			heatmapData[region] = {};
			productTypes.forEach(productType => {
				const item = data.find(d => d.Region === region && d.ProductType === productType);
				const rate = item 
					? (typeof item.SuccessRate === 'number' && !isNaN(item.SuccessRate)
						? item.SuccessRate
						: typeof item.SuccessRate === 'string'
							? parseFloat(item.SuccessRate) || 0
							: 0)
					: null;
				
				if (rate !== null) {
					heatmapData[region][productType] = rate;
					maxValue = Math.max(maxValue, rate);
					minValue = Math.min(minValue, rate);
				}
			});
		});

		return { regions, productTypes, heatmapData, maxValue, minValue };
	});

	const { regions, productTypes, heatmapData, maxValue, minValue } = processedData;
</script>

<div class="heatmap-container" style="height: {height};">
	{#if regions.length === 0 || productTypes.length === 0}
		<div class="no-data">
			<p>No heatmap data available</p>
		</div>
	{:else}
		<div class="heatmap-wrapper">
			<div class="heatmap-header">
				<div class="corner-label"></div>
				<div class="product-labels">
					{#each productTypes as productType}
						<div class="product-label">{productType}</div>
					{/each}
				</div>
			</div>
			<div class="heatmap-body">
				{#each regions as region}
					<div class="heatmap-row">
						<div class="region-label">{region}</div>
						<div class="heatmap-cells">
							{#each productTypes as productType}
								{@const rate = heatmapData[region]?.[productType] ?? null}
								{@const color = rate !== null ? getColorIntensity(rate) : 'rgba(55, 65, 81, 0.3)'}
								<div 
									class="heatmap-cell {rate === null ? 'no-data-cell' : 'clickable'}"
									style="background-color: {color};"
									title="{region} x {productType}: {rate !== null ? rate.toFixed(1) + '%' : 'No data'}"
									onclick={() => rate !== null && handleCellClick(region, productType)}
									role={rate !== null ? 'button' : undefined}
									tabindex={rate !== null ? 0 : undefined}
									onkeydown={(e) => {
										if (rate !== null && (e.key === 'Enter' || e.key === ' ')) {
											e.preventDefault();
											handleCellClick(region, productType);
										}
									}}
								>
									<span class="cell-value">{rate !== null ? rate.toFixed(0) + '%' : '-'}</span>
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
				<span class="legend-range">({minValue.toFixed(0)}% - {maxValue.toFixed(0)}%)</span>
			</div>
		</div>
	{/if}
</div>

{#if showErrorModal}
	<ErrorDetailsPanel
		isOpen={showErrorModal}
		title={selectedRegion && selectedProductType ? `${selectedRegion} - ${selectedProductType}` : 'Error Details'}
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
	}

	/* Custom scrollbar styling with theme */
	.heatmap-container::-webkit-scrollbar {
		height: 10px;
	}

	.heatmap-container::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 5px;
	}

	.heatmap-container::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.heatmap-container::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	/* Firefox scrollbar */
	.heatmap-container {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.heatmap-wrapper {
		min-width: 100%;
	}

	.heatmap-header {
		margin-bottom: 0.5rem;
		display: flex;
	}

	.corner-label {
		width: 160px;
		flex-shrink: 0;
	}

	.product-labels {
		display: flex;
		gap: 2px;
		padding-left: 0.5rem;
		flex: 1;
	}

	.product-label {
		font-size: 1rem;
		color: #9ca3af;
		font-weight: 500;
		min-width: 120px;
		text-align: center;
		padding: 0.75rem;
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
		min-width: 120px;
		height: 80px;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: transform 0.1s, box-shadow 0.1s;
		border: 1px solid rgba(55, 65, 81, 0.5);
	}

	.heatmap-cell:hover {
		transform: scale(1.05);
		box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
		z-index: 10;
		position: relative;
	}

	.heatmap-cell.clickable {
		cursor: pointer;
	}

	.heatmap-cell.clickable:focus {
		outline: 2px solid #34d399;
		outline-offset: 2px;
	}

	.heatmap-cell.no-data-cell {
		cursor: default;
	}

	.heatmap-cell.no-data-cell:hover {
		transform: none;
		box-shadow: none;
	}

	.cell-value {
		font-size: 1rem;
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
			rgba(239, 68, 68, 0.8),
			rgba(249, 115, 22, 0.7),
			rgba(251, 191, 36, 0.6),
			rgba(34, 197, 94, 0.7),
			rgba(16, 185, 129, 0.8)
		);
		border-radius: 6px;
		border: 1px solid rgba(55, 65, 81, 0.5);
	}

	.legend-range {
		font-size: 0.7rem;
		color: #6b7280;
		margin-left: 0.5rem;
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

	.modal-overlay {
		position: fixed !important;
		top: 0 !important;
		left: 0 !important;
		right: 0 !important;
		bottom: 0 !important;
		width: 100vw !important;
		height: 100vh !important;
		background-color: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 99999 !important;
		overflow-y: auto;
		pointer-events: auto;
		margin: 0 !important;
		padding: 0 !important;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		transform: translateZ(0);
		-webkit-transform: translateZ(0);
		will-change: auto;
	}

	.modal-content {
		background-color: #1f2937;
		border-radius: 0.5rem;
		padding: 1rem;
		max-width: 600px;
		width: 90vw;
		max-height: 80vh;
		overflow-y: auto;
		border: 1px solid #374151;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		flex-shrink: 0;
		position: fixed !important;
		top: 50% !important;
		left: 50% !important;
		transform: translate(-50%, -50%) translateZ(0) !important;
		-webkit-transform: translate(-50%, -50%) translateZ(0) !important;
		margin: 0 !important;
		will-change: auto;
	}

	/* Custom scrollbar styling with theme */
	.modal-content::-webkit-scrollbar {
		width: 10px;
	}

	.modal-content::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 5px;
	}

	.modal-content::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.modal-content::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	/* Firefox scrollbar */
	.modal-content {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.loading-modal,
	.error-modal,
	.no-data-modal {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		min-width: 300px;
		text-align: center;
	}

	.loading-modal p,
	.error-modal p,
	.no-data-modal p {
		color: #9ca3af;
		margin: 0;
	}

	.error-modal h2,
	.no-data-modal h2 {
		color: #f87171;
		margin: 0 0 0.5rem 0;
	}

	.close-btn {
		padding: 0.5rem 1rem;
		background-color: var(--color-primary-dark);
		color: white;
		border: none;
		border-radius: 0.375rem;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 500;
		margin-top: 1rem;
		transition: background-color 0.2s;
	}

	.close-btn:hover {
		background-color: var(--color-primary);
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #374151;
		border-top-color: var(--color-primary-light);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>

