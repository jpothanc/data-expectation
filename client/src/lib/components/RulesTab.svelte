<script lang="ts">
	import { getRules, getRulesYaml, getCombinedRuleNames, getCombinedRuleDetails, getCombinedRuleDetailsYaml } from '../services/api';
	import { DEFAULT_EXCHANGE } from '../constants';
	import { exchangesStore, fetchExchanges, getDefaultExchange } from '../stores/exchanges.svelte';
	import { convertToTableData } from '../utils/table';
	import DataTable from './DataTable.svelte';
	import Select from './Select.svelte';

	interface Props {
		productType?: 'stock' | 'future' | 'option';
	}

	let { productType = 'stock' }: Props = $props();

	let selectedExchange = $state(DEFAULT_EXCHANGE);
	let ruleType = $state<'regular' | 'combined'>('regular');
	let viewMode = $state<'table' | 'yaml'>('table');
	let selectedCombinedRule = $state<string>('');
	let combinedRules = $state<string[]>([]);
	let loadingCombinedRules = $state(false);
	let filterText = $state<string>('');
	let loading = $state(false);
	let error = $state<string | null>(null);
	let rulesData = $state<any | null>(null);
	let yamlData = $state<string | null>(null);
	const INSTRUMENT_TYPE = productType;

	// Use shared exchanges store (direct access to reactive state)
	const exchanges = $derived.by(() => exchangesStore.exchanges);
	const loadingExchanges = $derived.by(() => exchangesStore.loading);

	async function fetchCombinedRuleNames() {
		loadingCombinedRules = true;
		selectedCombinedRule = '';
		rulesData = null;
		try {
			combinedRules = await getCombinedRuleNames(INSTRUMENT_TYPE, selectedExchange);
		} catch (err) {
			console.error('Failed to fetch combined rule names:', err);
			combinedRules = [];
		} finally {
			loadingCombinedRules = false;
		}
	}

	async function fetchRules() {
		loading = true;
		error = null;
		rulesData = null;
		yamlData = null;
		filterText = ''; // Reset filter when loading new data

		try {
			if (ruleType === 'combined') {
				if (!selectedCombinedRule) {
					error = 'Please select a combined rule';
					return;
				}
				// Combined rules - fetch based on view mode
				if (viewMode === 'yaml') {
					yamlData = await getCombinedRuleDetailsYaml(INSTRUMENT_TYPE, selectedExchange, selectedCombinedRule);
				} else {
					rulesData = await getCombinedRuleDetails(INSTRUMENT_TYPE, selectedExchange, selectedCombinedRule);
				}
			} else {
				// Regular rules - fetch based on view mode
				if (viewMode === 'yaml') {
					yamlData = await getRulesYaml(INSTRUMENT_TYPE, selectedExchange);
				} else {
					rulesData = await getRules(selectedExchange, INSTRUMENT_TYPE);
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
		}
	}

	// Fetch exchanges on mount (only once)
	let exchangesFetched = $state(false);
	$effect(() => {
		// Only fetch if not already initialized and not currently loading
		if (!exchangesStore.initialized && !exchangesStore.loading && !exchangesFetched) {
			exchangesFetched = true;
			fetchExchanges();
		}
	});
	
	// Set default exchange when exchanges are loaded (separate effect to avoid loop)
	$effect(() => {
		if (exchangesStore.initialized && exchanges.length > 0 && !exchanges.find(e => e.value === selectedExchange)) {
			selectedExchange = getDefaultExchange();
		}
	});

	// Fetch combined rule names when switching to combined rules or when exchange changes
	$effect(() => {
		if (ruleType === 'combined' && selectedExchange && exchanges.length > 0) {
			fetchCombinedRuleNames();
		} else {
			combinedRules = [];
			selectedCombinedRule = '';
		}
	});

	function getTableData() {
		if (!rulesData) {
			return { data: [], headers: [] };
		}

		let rawData: any[] = [];

		// Handle different response structures
		if (Array.isArray(rulesData)) {
			rawData = rulesData;
		} else if (rulesData && typeof rulesData === 'object') {
			// If it's an object, try to find an array property
			if (Array.isArray(rulesData.rules)) {
				rawData = rulesData.rules;
			} else if (Array.isArray(rulesData.data)) {
				rawData = rulesData.data;
			} else {
				// Convert single object to array
				rawData = [rulesData];
			}
		}

		// Filter by text if provided
		if (filterText && filterText.trim() !== '') {
			const searchText = filterText.toLowerCase().trim();
			rawData = rawData.filter(item => {
				if (!item || typeof item !== 'object') {
					return false;
				}
				// Search across all values in the row
				return Object.values(item).some(value => {
					if (value === null || value === undefined) {
						return false;
					}
					const stringValue = String(value).toLowerCase();
					return stringValue.includes(searchText);
				});
			});
		}

		return convertToTableData(rawData);
	}
</script>

<div class="rules-tab">
	<div class="controls">
		<Select 
			bind:value={selectedExchange}
			options={exchanges.map(ex => ({ value: ex.value, label: ex.label || ex.value }))}
			disabled={loading || loadingCombinedRules || loadingExchanges}
			placeholder={loadingExchanges ? 'Loading exchanges...' : 'Select exchange'}
		/>
		
		<Select 
			bind:value={ruleType}
			options={[
				{ value: 'regular', label: 'Regular Rules' },
				{ value: 'combined', label: 'Combined Rules' }
			]}
			disabled={loading || loadingCombinedRules}
		/>
		
		{#if ruleType === 'combined'}
			<Select 
				bind:value={selectedCombinedRule}
				options={combinedRules.map(rule => ({ value: rule, label: rule }))}
				disabled={loading || loadingCombinedRules || combinedRules.length === 0}
				placeholder={loadingCombinedRules ? 'Loading combined rules...' : combinedRules.length === 0 ? 'No combined rules available' : 'Select combined rule'}
			/>
		{/if}
		
		<Select 
			bind:value={viewMode}
			options={[
				{ value: 'table', label: 'Table View' },
				{ value: 'yaml', label: 'YAML View' }
			]}
			disabled={loading || (ruleType === 'combined' && !selectedCombinedRule)}
		/>
		
		<button 
			onclick={fetchRules} 
			disabled={loading || (ruleType === 'combined' && !selectedCombinedRule)}
			class="btn"
		>
			{loading ? 'Loading...' : 'Load Rules'}
		</button>
	</div>

	{#if rulesData && viewMode === 'table'}
		<div class="filter-controls">
			<label for="text-filter" class="filter-label">Filter:</label>
			<input 
				id="text-filter"
				type="text"
				bind:value={filterText}
				placeholder="Type to filter table rows..."
				disabled={loading}
				class="filter-input"
			/>
			{#if filterText}
				<button 
					onclick={() => filterText = ''}
					class="clear-filter-btn"
					type="button"
					title="Clear filter"
				>
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			{/if}
		</div>
	{/if}

	{#if error}
		<div class="error">
			<p>Error: {error}</p>
		</div>
	{/if}

	{#if yamlData}
		<div class="yaml-container">
			<div class="yaml-header">
				<h3>
					{ruleType === 'combined' && selectedCombinedRule 
						? `Combined Rule: ${selectedCombinedRule} (YAML)` 
						: 'Rules in YAML Format'}
				</h3>
				<button 
					onclick={() => {
						navigator.clipboard.writeText(yamlData);
					}}
					class="copy-btn"
					type="button"
					title="Copy to clipboard"
				>
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
					</svg>
					Copy
				</button>
			</div>
			<pre class="yaml-content"><code>{yamlData}</code></pre>
		</div>
	{/if}

	{#if rulesData && viewMode === 'table'}
		{@const tableData = getTableData()}
		{#if tableData.data.length > 0 && tableData.headers.length > 0}
			<DataTable 
				headers={tableData.headers}
				data={tableData.data}
				title="{ruleType === 'combined' ? 'Combined Rule' : 'Rules'} ({tableData.data.length}{filterText ? ' filtered' : ''}){ruleType === 'combined' && selectedCombinedRule ? ` - ${selectedCombinedRule}` : ''}"
			/>
		{:else}
			<div class="info-message">
				<p>
					{filterText ? 'No rules found matching your filter.' : 'No rules data available.'}
					{#if filterText}
						<button 
							onclick={() => filterText = ''}
							class="clear-filter-link"
							type="button"
						>
							Clear filter
						</button>
					{/if}
				</p>
			</div>
		{/if}
	{/if}
</div>

<style>
	.rules-tab {
		/* Container styles */
	}

	.controls {
		display: flex;
		gap: 1rem;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.filter-controls {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
		padding: 0.75rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
	}

	.filter-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #9ca3af;
		white-space: nowrap;
	}

	.filter-input {
		flex: 1;
		padding: 0.5rem 0.75rem;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		background-color: #1f2937;
		color: #e5e7eb;
		transition: border-color 0.2s, box-shadow 0.2s;
	}

	.filter-input::placeholder {
		color: #6b7280;
	}

	.filter-input:hover:not(:disabled) {
		border-color: var(--color-primary-light);
	}

	.filter-input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px var(--shadow-primary);
	}

	.filter-input:disabled {
		background-color: #1f2937;
		cursor: not-allowed;
		color: #6b7280;
		opacity: 0.6;
	}

	.clear-filter-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		padding: 0;
		background-color: transparent;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		cursor: pointer;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.clear-filter-btn:hover {
		background-color: #1f2937;
		border-color: var(--color-primary-light);
		color: var(--color-primary-light);
	}

	.clear-filter-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.btn {
		background-color: var(--color-primary);
		color: white;
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s, transform 0.1s;
		white-space: nowrap;
	}

	.btn:hover:not(:disabled) {
		background-color: var(--color-hover);
		transform: translateY(-1px);
	}

	.btn:active:not(:disabled) {
		transform: translateY(0);
	}

	.btn:disabled {
		background-color: #374151;
		cursor: not-allowed;
		color: #9ca3af;
		opacity: 0.6;
	}

	.error {
		margin-top: 1rem;
		margin-bottom: 1rem;
		padding: 0.75rem;
		background-color: #7f1d1d;
		border: 1px solid #dc2626;
		border-radius: 0.5rem;
		color: #fca5a5;
		font-size: 0.875rem;
	}

	.info-message {
		margin-top: 2rem;
		padding: 1.5rem;
		background-color: #1e3a5f;
		border: 1px solid var(--color-primary);
		border-radius: 0.5rem;
		color: #93c5fd;
		text-align: center;
	}

	.info-message p {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin: 0;
	}

	.clear-filter-link {
		background: none;
		border: none;
		color: var(--color-primary-light);
		cursor: pointer;
		text-decoration: underline;
		font-size: inherit;
		padding: 0;
		margin: 0;
		transition: color 0.2s;
	}

	.clear-filter-link:hover {
		color: var(--color-hover);
	}

	.yaml-container {
		margin-top: 1.5rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		overflow: hidden;
	}

	.yaml-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background-color: #1f2937;
		border-bottom: 1px solid #374151;
	}

	.yaml-header h3 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #e5e7eb;
	}

	.copy-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background-color: var(--color-primary);
		color: white;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s, transform 0.1s;
	}

	.copy-btn:hover {
		background-color: var(--color-hover);
		transform: translateY(-1px);
	}

	.copy-btn:active {
		transform: translateY(0);
	}

	.copy-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.yaml-content {
		margin: 0;
		padding: 1.5rem;
		overflow-x: auto;
		background-color: #0f172a;
		color: #e2e8f0;
		font-family: 'Courier New', Courier, monospace;
		font-size: 0.875rem;
		line-height: 1.6;
		max-height: 70vh;
		overflow-y: auto;
		/* Firefox scrollbar */
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	/* Custom scrollbar styling with theme */
	.yaml-content::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}

	.yaml-content::-webkit-scrollbar-track {
		background-color: #111827;
		border-radius: 4px;
	}

	.yaml-content::-webkit-scrollbar-thumb {
		background-color: var(--color-primary-dark);
		border-radius: 4px;
		border: 1px solid #111827;
	}

	.yaml-content::-webkit-scrollbar-thumb:hover {
		background-color: var(--color-primary);
	}

	.yaml-content code {
		display: block;
		white-space: pre;
		color: inherit;
		font-family: inherit;
		font-size: inherit;
	}
</style>

