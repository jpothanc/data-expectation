<script lang="ts">
	import { getInstrumentsByExchange, getInstrumentById, getInstrumentByRic } from '../services/api';
	import { convertInstrumentsToTableData } from '../utils/table';
	import { DEFAULT_EXCHANGE } from '../constants';
	import { exchangesStore, fetchExchanges, getDefaultExchange } from '../stores/exchanges.svelte';
	import DataTable from './DataTable.svelte';
	import Select from './Select.svelte';

	interface Props {
		productType?: 'stock' | 'future' | 'option';
	}

	let { productType = 'stock' }: Props = $props();

	let instrumentExchange = $state(DEFAULT_EXCHANGE);
	let instrumentId = $state('');
	let instrumentRic = $state('');
	let loading = $state(false);
	let error = $state<string | null>(null);
	let instrumentsData = $state<any[] | null>(null);

	// Use shared exchanges store (direct access to reactive state)
	const exchanges = $derived.by(() => exchangesStore.exchanges);
	const loadingExchanges = $derived.by(() => exchangesStore.loading);

	async function fetchInstrumentsByExchange() {
		loading = true;
		error = null;
		instrumentsData = null;

		try {
			instrumentsData = await getInstrumentsByExchange(instrumentExchange, productType);
		} catch (err) {
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
		}
	}

	async function fetchInstrumentById() {
		if (!instrumentId.trim()) {
			error = 'Please enter an Instrument ID';
			return;
		}

		loading = true;
		error = null;
		instrumentsData = null;

		try {
			instrumentsData = await getInstrumentById(instrumentId.trim(), instrumentExchange, productType);
		} catch (err) {
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
		}
	}

	async function fetchInstrumentByRic() {
		if (!instrumentRic.trim()) {
			error = 'Please enter a RIC code';
			return;
		}

		loading = true;
		error = null;
		instrumentsData = null;

		try {
			instrumentsData = await getInstrumentByRic(instrumentRic.trim(), instrumentExchange, productType);
		} catch (err) {
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
		}
	}

	function getTableData() {
		if (!instrumentsData || instrumentsData.length === 0) {
			return { data: [], headers: [] };
		}
		return convertInstrumentsToTableData(instrumentsData);
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
		if (exchangesStore.initialized && exchanges.length > 0 && !exchanges.find(e => e.value === instrumentExchange)) {
			instrumentExchange = getDefaultExchange();
		}
	});
</script>

<div class="instruments-tab">
	<div class="search-container">
		<div class="search-row">
			<div class="search-item">
				<label for="instrument-exchange" class="search-label">Exchange</label>
				<div class="search-input-group">
					<Select 
						id="instrument-exchange"
						bind:value={instrumentExchange}
						options={exchanges.map(ex => ({ value: ex.value, label: ex.label || ex.value }))}
						disabled={loading || loadingExchanges}
						placeholder={loadingExchanges ? 'Loading exchanges...' : 'Select exchange'}
					/>
					<button 
						onclick={fetchInstrumentsByExchange} 
						disabled={loading}
						class="btn btn-sm"
						title="Search by Exchange"
					>
						{loading ? '...' : 'Search'}
					</button>
				</div>
			</div>

			<div class="search-item">
				<label for="instrument-id" class="search-label">Instrument ID</label>
				<div class="search-input-group">
					<input 
						id="instrument-id"
						type="text"
						bind:value={instrumentId}
						placeholder="e.g., HK0001"
						disabled={loading}
						class="input-field"
						onkeydown={(e) => e.key === 'Enter' && fetchInstrumentById()}
					/>
					<button 
						onclick={fetchInstrumentById} 
						disabled={loading}
						class="btn btn-sm"
						title="Search by Instrument ID"
					>
						{loading ? '...' : 'Search'}
					</button>
				</div>
			</div>

			<div class="search-item">
				<label for="instrument-ric" class="search-label">RIC</label>
				<div class="search-input-group">
					<input 
						id="instrument-ric"
						type="text"
						bind:value={instrumentRic}
						placeholder="e.g., 0005.HK"
						disabled={loading}
						class="input-field"
						onkeydown={(e) => e.key === 'Enter' && fetchInstrumentByRic()}
					/>
					<button 
						onclick={fetchInstrumentByRic} 
						disabled={loading}
						class="btn btn-sm"
						title="Search by RIC"
					>
						{loading ? '...' : 'Search'}
					</button>
				</div>
			</div>
		</div>
	</div>

	{#if error}
		<div class="error">
			<p>Error: {error}</p>
		</div>
	{/if}

	{#if instrumentsData}
		{@const tableData = getTableData()}
		{#if tableData.data.length > 0 && tableData.headers.length > 0}
			<DataTable 
				headers={tableData.headers}
				data={tableData.data}
				title="Instruments ({tableData.data.length})"
				ricColumn="RIC"
			/>
		{:else}
			<div class="info-message">
				<p>No instruments found.</p>
			</div>
		{/if}
	{/if}
</div>

<style>
	.search-container {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
	}

	.search-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
		align-items: start;
	}

	.search-item {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.search-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		line-height: 1.2;
		margin-bottom: 0;
	}

	.search-input-group {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}


	.input-field {
		flex: 1;
		padding: 0.5rem 0.75rem;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		background-color: #1f2937;
		color: #e5e7eb;
		transition: border-color 0.2s, box-shadow 0.2s;
		height: 2.5rem;
		box-sizing: border-box;
	}

	.input-field::placeholder {
		color: #6b7280;
	}

	.input-field:hover:not(:disabled) {
		border-color: var(--color-primary-light);
	}

	.input-field:focus {
		outline: none;
		border-color: var(--color-primary-light);
		box-shadow: 0 0 0 3px var(--shadow-primary);
	}

	.input-field:disabled {
		background-color: #1f2937;
		cursor: not-allowed;
		color: #6b7280;
	}

	.btn {
		background-color: var(--color-primary-dark);
		color: white;
		padding: 0.4375rem 0.875rem;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.8125rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
		white-space: nowrap;
	}

	.btn-sm {
		padding: 0.4375rem 0.75rem;
		font-size: 0.75rem;
		height: 2.5rem;
		box-sizing: border-box;
		display: flex;
		align-items: center;
		justify-content: center;
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
		background-color: rgba(30, 58, 95, 0.3);
		border: 1px solid var(--color-primary);
		border-radius: 0.5rem;
		color: #93c5fd;
		text-align: center;
	}

	@media (max-width: 768px) {
		.search-row {
			grid-template-columns: 1fr;
		}
	}
</style>

