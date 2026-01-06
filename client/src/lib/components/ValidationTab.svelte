<script lang="ts">
	import { validateStocks, validateFutures, validateOptions, validateCustom, validateByMasterId, getCombinedRuleNames, validateCombinedRule } from '../services/api';
	import { DEFAULT_EXCHANGE } from '../constants';
	import { exchangesStore, fetchExchanges, getDefaultExchange } from '../stores/exchanges.svelte';
	import type { ValidationResponse, ValidationResult } from '../types';
	import {
		filterValidationResults,
		transformValidationResultsToTableData,
		formatHeaderName
	} from '../utils';
	import DataTable from './DataTable.svelte';
	import SummaryCard from './SummaryCard.svelte';
	import Select from './Select.svelte';
	import PartialDataModal from './PartialDataModal.svelte';

	interface Props {
		initialExchange?: string | null;
		productType?: 'stock' | 'future' | 'option';
	}

	let { initialExchange = null, productType = 'stock' }: Props = $props();

	let selectedExchange = $state(DEFAULT_EXCHANGE);
	let selectedRule = $state<string>('exchange');
	let masterId = $state<string>('');
	let loading = $state(false);
	let loadingRules = $state(false);
	let error = $state<string | null>(null);
	let data = $state<ValidationResponse | null>(null);
	let expectationResults = $state<ValidationResult[]>([]);
	let showFailedOnly = $state(true);
	let modalOpen = $state(false);
	let modalData = $state<string>('');
	let modalHeader = $state<string>('');
	let allRules = $state<string[]>([]);
	const INSTRUMENT_TYPE = productType;
	const EXCHANGE_RULE = 'exchange';

	// Use shared exchanges store
	const exchanges = $derived.by(() => exchangesStore.getExchanges(productType));
	const loadingExchanges = $derived.by(() => exchangesStore.isLoading(productType));

	function openModal(data: string, header: string) {
		modalData = data;
		modalHeader = header;
		modalOpen = true;
	}

	function closeModal() {
		modalOpen = false;
		modalData = '';
		modalHeader = '';
	}

	function truncateText(text: string, maxLength: number = 50): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}


	async function fetchAllRules() {
		loadingRules = true;
		selectedRule = EXCHANGE_RULE; // Reset to exchange when fetching new rules
		try {
			const rules = await getCombinedRuleNames(INSTRUMENT_TYPE, selectedExchange);
			allRules = rules;
		} catch (err) {
			console.error('Failed to fetch rules:', err);
			allRules = [];
		} finally {
			loadingRules = false;
		}
	}

	async function fetchStocks() {
		loading = true;
		error = null;
		data = null;
		expectationResults = [];
		showFailedOnly = true; // Reset to show failed first

		try {
			let response: ValidationResponse;
			
			// If master ID is provided, use master ID validation API
			if (masterId && masterId.trim() !== '') {
				const ruleName = selectedRule === EXCHANGE_RULE 
					? (productType === 'future' ? 'is_tradable_futures' : productType === 'option' ? 'is_tradable_options' : 'is_tradable_stocks')
					: selectedRule;
				response = await validateByMasterId(masterId.trim(), ruleName);
			} else {
				// Otherwise, use exchange-based validation
				if (selectedRule === EXCHANGE_RULE) {
					// Use the standard exchange validation API based on product type
					if (productType === 'future') {
						response = await validateFutures(selectedExchange);
					} else if (productType === 'option') {
						response = await validateOptions(selectedExchange);
					} else {
						response = await validateStocks(selectedExchange);
					}
				} else {
					// Use combined rule validation API
					if (!selectedRule) {
						throw new Error('Please select a rule');
					}
					response = await validateCombinedRule(INSTRUMENT_TYPE, selectedExchange, selectedRule);
				}
			}
			
			data = response;
			
			// Extract expectation results if they exist
			if (response?.results?.expectation_results) {
				expectationResults = response.results.expectation_results;
			} else if (Array.isArray(response)) {
				expectationResults = response;
			}
			
			// Debug: log first result to see structure
			if (expectationResults.length > 0) {
				console.log('First validation result:', expectationResults[0]);
				console.log('Result field type:', typeof expectationResults[0].result);
				console.log('Result field value:', expectationResults[0].result);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
		}
	}

	// Initialize exchange from prop if provided and trigger validation
	let hasInitialized = $state(false);
	$effect(() => {
		if (initialExchange && !hasInitialized) {
			selectedExchange = initialExchange;
			hasInitialized = true;
			// Trigger validation after a short delay to ensure component is mounted
			setTimeout(() => {
				fetchStocks();
			}, 100);
		}
	});

	// Fetch exchanges on mount (only once)
	let exchangesFetched = $state(false);
	$effect(() => {
		// Only fetch if not already initialized and not currently loading
		if (!exchangesStore.isInitialized(productType) && !exchangesStore.isLoading(productType) && !exchangesFetched) {
			exchangesFetched = true;
			fetchExchanges(productType);
		}
	});
	
	// Set default exchange when exchanges are loaded (separate effect to avoid loop)
	$effect(() => {
		if (exchangesStore.isInitialized(productType) && exchanges.length > 0 && !exchanges.find(e => e.value === selectedExchange)) {
			selectedExchange = getDefaultExchange(productType);
		}
	});

	// Fetch all rules when exchange changes
	$effect(() => {
		if (selectedExchange && exchanges.length > 0) {
			fetchAllRules();
		}
	});

	function getSummaryItems(): Array<{ label: string; value: string | number; highlight?: 'success' | 'failed' | 'info' }> {
		if (!data) return [];
		
		return [
			{ label: 'Exchange', value: data.exchange || 'N/A' },
			{ 
				label: 'Overall Status', 
				value: data.success ? '✓ Passed' : '✗ Failed',
				highlight: (data.success ? 'success' : 'failed') as 'success' | 'failed'
			},
			{ label: 'Total Expectations', value: data.total_expectations || 0 },
			{ label: 'Successful', value: data.successful_expectations || 0, highlight: 'success' as const },
			{ label: 'Failed', value: data.failed_expectations || 0, highlight: 'failed' as const }
		];
	}

	const filteredResults = $derived.by(() => {
		const results = filterValidationResults(expectationResults, showFailedOnly);
		// Sort: failed first, then successful (create a copy to avoid mutating original)
		return [...results].sort((a, b) => {
			if (a.success === b.success) return 0;
			return a.success ? 1 : -1; // false (failed) comes before true (success)
		});
	});

	const tableData = $derived.by(() => {
		return transformValidationResultsToTableData(filteredResults);
	});

	const failedCount = $derived(expectationResults.filter(r => !r.success).length);
</script>

<div class="validation-tab">
	<div class="controls">
		<Select 
			bind:value={selectedExchange}
			options={exchanges.map(ex => ({ value: ex.value, label: ex.label || ex.value }))}
			disabled={loading || loadingRules || loadingExchanges || !!(masterId && masterId.trim() !== '')}
			placeholder={loadingExchanges ? 'Loading exchanges...' : 'Select exchange'}
		/>
		
		<input
			type="text"
			bind:value={masterId}
			placeholder="Master ID (optional)"
			class="master-id-input"
			disabled={loading}
		/>
		
		<Select 
			id="rule-select"
			bind:value={selectedRule}
			options={[
				{ value: EXCHANGE_RULE, label: 'Exchange' },
				...allRules.map(rule => ({ value: rule, label: rule }))
			]}
			disabled={loading || loadingRules}
			placeholder={loadingRules ? 'Loading rules...' : 'Select rule'}
		/>
		
		<button 
			onclick={fetchStocks} 
			disabled={loading}
			class="btn"
		>
			{loading ? 'Loading...' : 'Validate Stocks'}
		</button>
	</div>

	{#if error}
		<div class="error">
			<p>Error: {error}</p>
		</div>
	{/if}

	{#if data}
		{#if data.exchange || data.total_expectations !== undefined}
			<SummaryCard items={getSummaryItems()} />
		{/if}

		{#if expectationResults.length > 0}
			<div class="table-wrapper">
				<div class="table-header">
					<h2 class="table-title">
						Validation Results
					</h2>
					<div class="table-actions">
						<button 
							class="filter-btn {showFailedOnly ? 'active' : ''}"
							onclick={() => {
								showFailedOnly = !showFailedOnly;
							}}
							title={showFailedOnly ? 'Show all validations' : 'Show only failed validations'}
							type="button"
						>
							{showFailedOnly ? `Show All (${expectationResults.length})` : `Show Failed Only (${failedCount})`}
						</button>
					</div>
				</div>
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								{#each tableData.headers as header}
									<th>{formatHeaderName(header)}</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each tableData.data as row}
								<tr class="result-row {row._success ? 'success-row' : 'failed-row'}">
									{#each tableData.headers as header}
										<td class={header === 'column' ? 'column-name' : header === 'expectationType' ? 'expectation-type' : header.startsWith('partial_') || header.includes('percent') ? 'detail-value' : ''}>
									{#if header === 'status'}
										<span class="status-indicator {row._success ? 'success' : 'failed'}">
											{row[header] || '—'}
										</span>
									{:else}
										{#if row[header] !== undefined && row[header] !== null && row[header] !== ''}
											{#if header === 'partial_unexpected_counts'}
												<div class="partial-data-cell">
													<span class="partial-preview">{truncateText(String(row[header]), 40)}</span>
													<button
														class="view-details-btn"
														onclick={() => openModal(String(row[header]), header)}
														type="button"
														title="View full details"
													>
														<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
														</svg>
													</button>
												</div>
											{:else if header.startsWith('partial_')}
												<div class="partial-data-cell">
													<span class="partial-preview">{truncateText(String(row[header]), 40)}</span>
													<button
														class="view-details-btn"
														onclick={() => openModal(String(row[header]), header)}
														type="button"
														title="View full details"
													>
														<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
														</svg>
													</button>
												</div>
											{:else}
												<div class="cell-content-wrapper">
													<span class="cell-value">{row[header]}</span>
													{#if header.includes('unexpected') || header.includes('percent') || header === 'column' || header === 'expectationType'}
														<span class="tooltip-icon-wrapper" title={formatHeaderName(header)}>
															<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="tooltip-icon">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
															</svg>
														</span>
													{/if}
												</div>
											{/if}
										{:else}
											<span class="empty-value">—</span>
										{/if}
									{/if}
										</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	{/if}

	<PartialDataModal data={modalData} header={modalHeader} open={modalOpen} onClose={closeModal} />
</div>

<style>
	.controls {
		display: flex;
		gap: 1rem;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.master-id-input {
		padding: 0.5rem 1rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #e5e7eb;
		font-size: 0.875rem;
		min-width: 150px;
		transition: border-color 0.2s;
	}

	.master-id-input:focus {
		outline: none;
		border-color: var(--color-primary-light);
	}

	.master-id-input:disabled {
		background-color: #111827;
		border-color: #1f2937;
		color: #6b7280;
		cursor: not-allowed;
	}

	.master-id-input::placeholder {
		color: #6b7280;
	}


	.btn {
		background-color: var(--color-primary-dark);
		color: white;
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
		white-space: nowrap;
	}

	.btn:hover:not(:disabled) {
		background-color: var(--color-primary);
	}

	.btn:disabled {
		background-color: #374151;
		cursor: not-allowed;
		color: #9ca3af;
	}

	.error {
		margin-top: 1.5rem;
		padding: 1rem;
		background-color: #7f1d1d;
		border: 1px solid #dc2626;
		border-radius: 0.5rem;
		color: #fca5a5;
	}

	.table-wrapper {
		margin-top: 2rem;
	}

	.table-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding: 0 0.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.table-title {
		font-size: 1rem;
		font-weight: 600;
		color: #ffffff;
		margin: 0;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.total-count-badge {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-primary-light);
	}

	.count-badge {
		font-size: 0.875rem;
		font-weight: 400;
		color: #9ca3af;
	}

	.filter-badge {
		font-size: 0.875rem;
		font-weight: 500;
		color: #f87171;
	}

	.table-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.filter-btn {
		padding: 0.5rem 1rem;
		background-color: #1f2937;
		color: #e5e7eb;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.filter-btn:hover:not(:disabled) {
		background-color: #374151;
		border-color: var(--color-primary-light);
		color: #ffffff;
	}

	.filter-btn.active {
		background-color: #7f1d1d;
		border-color: #dc2626;
		color: #fca5a5;
	}

	.filter-btn.active:hover {
		background-color: #991b1b;
		border-color: #f87171;
	}

	.filter-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.table-container {
		border: 1px solid #374151;
		border-radius: 0.5rem;
		overflow: auto;
		max-height: 600px;
		background-color: #111827;
		scrollbar-width: thin;
		scrollbar-color: #4b5563 #111827;
	}

	.table-container::-webkit-scrollbar {
		width: 12px;
		height: 12px;
	}

	.table-container::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 6px;
	}

	.table-container::-webkit-scrollbar-thumb {
		background: #4b5563;
		border-radius: 6px;
		border: 2px solid #111827;
	}

	.table-container::-webkit-scrollbar-thumb:hover {
		background: #6b7280;
	}

	.table-container::-webkit-scrollbar-corner {
		background: #111827;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.data-table thead {
		position: sticky;
		top: -1px;
		background-color: #1f2937;
		z-index: 10;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
	}

	.data-table thead tr {
		position: relative;
	}

	.data-table th {
		padding: 0.75rem 1rem;
		text-align: left;
		font-weight: 600;
		color: #e5e7eb;
		border-bottom: 2px solid #4b5563;
		background-color: #1f2937;
		white-space: nowrap;
		border-top: 1px solid #374151;
	}

	.data-table td {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #374151;
		color: #e5e7eb;
		word-break: break-word;
		max-width: none;
	}

	.data-table tbody tr.success-row {
		background-color: transparent;
	}

	.data-table tbody tr.failed-row {
		background-color: #7f1d1d;
	}

	.data-table tbody tr.success-row:hover {
		background-color: #1f2937;
	}

	.data-table tbody tr.failed-row:hover {
		background-color: #991b1b;
	}

	.data-table tbody tr:last-child td {
		border-bottom: none;
	}

	.status-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.5rem;
		height: 1.5rem;
		border-radius: 50%;
		font-weight: bold;
		font-size: 0.875rem;
	}

	.status-indicator.success {
		background-color: #065f46;
		color: #34d399;
	}

	.status-indicator.failed {
		background-color: #991b1b;
		color: #fca5a5;
	}

	.column-name {
		font-weight: 600;
		color: #ffffff;
	}

	.expectation-type {
		font-family: 'Courier New', monospace;
		font-size: 0.8125rem;
		color: #9ca3af;
	}

	.detail-value {
		font-size: 0.8125rem;
		color: #9ca3af;
		white-space: normal;
		word-wrap: break-word;
		word-break: break-word;
		max-width: none;
		line-height: 1.5;
		min-width: 200px;
	}

	.partial-data-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.partial-preview {
		font-family: 'Courier New', monospace;
		font-size: 0.8125rem;
		color: #9ca3af;
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.view-details-btn {
		background: none;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		color: #34d399;
		cursor: pointer;
		padding: 0.25rem 0.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.view-details-btn:hover {
		background-color: #1f2937;
		border-color: var(--color-primary-light);
		color: #93c5fd;
	}

	.view-details-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.cell-content-wrapper {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
	}

	.cell-value {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.tooltip-icon-wrapper {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		color: #34d399;
		opacity: 0.6;
		flex-shrink: 0;
		cursor: help;
		transition: opacity 0.2s;
	}

	.tooltip-icon-wrapper:hover {
		opacity: 1;
	}

	.tooltip-icon {
		width: 0.875rem;
		height: 0.875rem;
	}

	.result-details {
		font-size: 0.8125rem;
		color: #9ca3af;
		white-space: normal;
		word-wrap: break-word;
		word-break: break-word;
		max-width: none;
		line-height: 1.5;
	}
</style>

