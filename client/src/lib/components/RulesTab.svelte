<script lang="ts">
	import { getRules, getRulesYaml, getCombinedRuleNames, getCombinedRuleDetails, getCombinedRuleDetailsYaml } from '../services/api';
	import { DEFAULT_EXCHANGE } from '../constants';
	import { exchangesStore, setupExchangeInit } from '../stores/exchanges.svelte';
	import { convertToTableData } from '../utils/table';
	import DataTable from './DataTable.svelte';
	import Select from './Select.svelte';

	interface Props {
		productType?: 'stock' | 'future' | 'option' | 'multileg';
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
	let yamlCopied = $state(false);
	const INSTRUMENT_TYPE = productType;

	function highlightYaml(src: string): string {
		return src
			.split('\n')
			.map((raw) => {
				const line = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
				if (!line.trim()) return line;
				if (line.trimStart().startsWith('#')) return `<span class="y-comment">${line}</span>`;
				const kvMatch = line.match(/^(\s*(?:-\s+)?)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:.*)$/);
				if (kvMatch) {
					const [, indent, key, rest] = kvMatch;
					const coloredRest = rest.replace(
						/^(\s*:\s*)(.+)?$/,
						(_, colon, val) => val ? `${colon}<span class="y-value">${val}</span>` : colon
					);
					return `${indent}<span class="y-key">${key}</span>${coloredRest}`;
				}
				const liMatch = line.match(/^(\s*)(-)(\s+.+)$/);
				if (liMatch) {
					const [, indent, dash, rest] = liMatch;
					return `${indent}<span class="y-dash">${dash}</span><span class="y-list-val">${rest}</span>`;
				}
				return line;
			})
			.join('\n');
	}

	async function copyYaml() {
		if (!yamlData) return;
		try {
			await navigator.clipboard.writeText(yamlData);
			yamlCopied = true;
			setTimeout(() => (yamlCopied = false), 2000);
		} catch { /* clipboard unavailable */ }
	}

	// Use shared exchanges store (per-product-type access)
	const exchanges = $derived.by(() => exchangesStore.getExchanges(productType));
	const loadingExchanges = $derived.by(() => exchangesStore.isLoading(productType));

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

	setupExchangeInit(productType, () => selectedExchange, (v) => { selectedExchange = v; });

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
						? `Combined Rule: ${selectedCombinedRule}`
						: 'Rules — YAML'}
				</h3>
				<button onclick={copyYaml} class="copy-btn" type="button">
					{#if yamlCopied}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
						</svg>
						Copied
					{:else}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
						</svg>
						Copy
					{/if}
				</button>
			</div>
			<pre class="yaml-content">{@html highlightYaml(yamlData)}</pre>
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
	.controls {
		display: flex;
		gap: 0.625rem;
		align-items: center;
		margin-bottom: 0.875rem;
		flex-wrap: wrap;
	}

	.filter-controls {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.875rem;
		padding: 0.5rem 0.75rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
	}

	.filter-label {
		font-size: 0.8125rem;
		font-weight: 500;
		color: #9ca3af;
		white-space: nowrap;
	}

	.filter-input {
		flex: 1;
		padding: 0.375rem 0.625rem;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.8125rem;
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
		padding: 0.375rem 0.875rem;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.8125rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s, transform 0.1s;
		white-space: nowrap;
		height: 2rem;
		box-sizing: border-box;
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
		margin-top: 1rem;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		overflow: hidden;
	}

	.yaml-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.625rem 1.25rem;
		background-color: #111827;
		border-bottom: 1px solid #1f2937;
	}

	.yaml-header h3 {
		margin: 0;
		font-size: 0.8125rem;
		font-weight: 600;
		color: #fff;
	}

	.copy-btn {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #d1d5db;
		font-size: 0.75rem;
		padding: 0.3rem 0.75rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.copy-btn:hover {
		background: #374151;
		color: #fff;
	}

	.copy-btn svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	.yaml-content {
		margin: 0;
		padding: 1rem 1.25rem;
		overflow-x: auto;
		overflow-y: auto;
		background: #0d1117;
		color: #e5e7eb;
		font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
		font-size: 0.75rem;
		line-height: 1.7;
		max-height: 70vh;
		white-space: pre;
		tab-size: 2;
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #0d1117;
	}

	.yaml-content::-webkit-scrollbar { width: 8px; height: 8px; }
	.yaml-content::-webkit-scrollbar-track { background: #0d1117; }
	.yaml-content::-webkit-scrollbar-thumb { background: var(--color-primary-dark); border-radius: 4px; }
	.yaml-content::-webkit-scrollbar-thumb:hover { background: var(--color-primary); }

	:global(.y-comment) { color: #6b7280; font-style: italic; }
	:global(.y-key)     { color: #60a5fa; font-weight: 600; }
	:global(.y-value)   { color: #a3e635; }
	:global(.y-dash)    { color: #f59e0b; }
	:global(.y-list-val){ color: #e5e7eb; }
</style>

