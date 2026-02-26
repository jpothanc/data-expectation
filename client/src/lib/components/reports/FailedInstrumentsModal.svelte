<script lang="ts">
	import { onMount } from 'svelte';
	import { API_BASE_URL, API_ENDPOINTS } from '$lib/constants';
	import InstrumentDetailsModal from '$lib/components/modals/InstrumentDetailsModal.svelte';
	import RuleYamlModal from './RuleYamlModal.svelte';
	import { getColumnsForProductType } from '$lib/config/failedInstrumentColumns';

	const FETCH_TIMEOUT_MS = 30_000;

	interface Props {
		columnName: string;
		expectationType: string;
		unexpectedCount: number;
		unexpectedPercent: number;
		missingCount: number;
		/** Pre-parsed unexpected value breakdown — pass [] if not available */
		unexpectedValues: { value: string; count: number }[];
		exchange: string;
		productType: string;
		onClose: () => void;
	}

	let {
		columnName,
		expectationType,
		unexpectedCount,
		unexpectedPercent,
		missingCount,
		unexpectedValues,
		exchange,
		productType,
		onClose
	}: Props = $props();

	// Normalise productType: DB may store "Stock" / "STOCK" / "futures" / null etc.
	const normalisedProductType = $derived((productType ?? 'stock').toLowerCase().replace(/s$/, '') || 'stock');

	// True when the expectation is specifically checking for null / missing values.
	// For these types (e.g. ExpectColumnValuesToNotBeNull) we should look up
	// instruments with null column values even if there are no other unexpected values.
	// For other types (e.g. ExpectColumnValuesToBeUnique) a non-zero MissingCount is
	// incidental — looking up null rows would return irrelevant data and may hang.
	const isNullCheckExpectation = $derived(
		expectationType.toLowerCase().includes('null') ||
		expectationType.toLowerCase().includes('none') ||
		expectationType.toLowerCase().includes('missing')
	);

	// True when the expectation checks for uniqueness (e.g. ExpectColumnValuesToBeUnique).
	// The "unexpected values" in this case ARE the duplicate IDs — the results will
	// intentionally contain multiple rows with the same column value.
	const isUniqueExpectation = $derived(
		expectationType.toLowerCase().includes('unique')
	);

	// ── Core state ─────────────────────────────────────────────
	let loading = $state(true);
	let error = $state<string | null>(null);
	let failedInstruments = $state<Record<string, any>[]>([]);
	let noDetailAvailable = $state(false);

	// ── Pagination & search ────────────────────────────────────
	const PAGE_SIZES = [25, 50, 100, 200] as const;
	let pageSize = $state<number>(50);
	let currentPage = $state(1);
	let searchQuery = $state('');
	let exporting = $state(false);

	// Instrument detail modal — opened inline from already-loaded data, no extra API call needed
	let selectedInstrument = $state<Record<string, any> | null>(null);

	// Rule YAML viewer — opened when the column badge is clicked
	let showRuleYaml = $state(false);

	const hasMissingValues = $derived(missingCount > 0);
	const unexpectedValueStrings = $derived(unexpectedValues.map((u) => u.value));

	// Abort controller so we can cancel in-flight fetch
	let abortController: AbortController | null = null;
	let userCancelled = false;

	function handleCancel() {
		userCancelled = true;
		abortController?.abort();
		onClose();
	}

	// ── Derived views ──────────────────────────────────────────
	/** Search-filtered instruments (all pages) */
	const filteredInstruments = $derived.by(() => {
		const q = searchQuery.trim().toLowerCase();
		if (!q) return failedInstruments;
		return failedInstruments.filter((inst) =>
			displayColumns.some((col) => String(inst[col] ?? '').toLowerCase().includes(q))
		);
	});

	const totalPages = $derived(Math.max(1, Math.ceil(filteredInstruments.length / pageSize)));

	/** Single page slice rendered in the DOM */
	const pageInstruments = $derived.by(() => {
		const start = (currentPage - 1) * pageSize;
		return filteredInstruments.slice(start, start + pageSize);
	});

	// Reset page when search or page size changes
	$effect(() => {
		searchQuery; // track
		pageSize;    // track
		currentPage = 1;
	});

	// Columns to display, driven by per-product-type config with DEFAULT_COLUMNS as fallback.
	// The failing column is always included. Columns absent from the payload are dropped.
	const displayColumns = $derived.by(() => {
		const availableKeys = failedInstruments.length > 0 ? Object.keys(failedInstruments[0]) : [];
		return getColumnsForProductType(normalisedProductType, columnName, availableKeys);
	});

	// ── Load + filter instruments ──────────────────────────────
	// Uses the server-side /filter endpoint so only matching instruments
	// are transferred — avoids fetching thousands of rows from large exchanges.
	async function loadInstruments() {
		const values  = unexpectedValueStrings;
		const rawMissing = hasMissingValues;

		// Only include the missing-value filter when the expectation is specifically
		// about null/missing checks (e.g. ExpectColumnValuesToNotBeNull).
		// For uniqueness checks the MissingCount is incidental — querying all
		// null-column rows is irrelevant and can hang on large exchanges.
		const missing = rawMissing && (values.length > 0 || isNullCheckExpectation);

		if (values.length === 0 && !missing) {
			noDetailAvailable = true;
			loading = false;
			return;
		}

		// Cancel any in-flight request before starting a new one
		abortController?.abort();
		abortController = new AbortController();
		const { signal } = abortController;

		loading = true;
		error = null;
		failedInstruments = [];

		// Manual timeout: abort after FETCH_TIMEOUT_MS
		const timeoutId = setTimeout(() => abortController?.abort(), FETCH_TIMEOUT_MS);

		try {
			// Build filter URL — server loads exchange data and returns only matching rows
			const base = `${API_BASE_URL}${API_ENDPOINTS.instrumentsByExchangeFilter}/${encodeURIComponent(exchange)}/filter`;
			const params = new URLSearchParams({
				product_type: normalisedProductType,
				column: columnName,
				missing: missing ? 'true' : 'false'
			});
			// Append each unexpected value as a separate `values=` parameter
			for (const v of values) {
				params.append('values', v);
			}

			const response = await fetch(`${base}?${params.toString()}`, { signal });
			clearTimeout(timeoutId);

			if (!response.ok) {
				throw new Error(`Server returned ${response.status} for ${exchange} / ${normalisedProductType}`);
			}

			const raw = await response.json();
			failedInstruments = Array.isArray(raw.instruments) ? raw.instruments : [];
			if (failedInstruments.length === 0 && !error) {
				noDetailAvailable = false; // use the "no matching instruments" path, not the "no detail" path
			}
		} catch (e: any) {
			clearTimeout(timeoutId);
			if (e?.name === 'AbortError') {
				if (!userCancelled) {
					// Timeout-triggered abort (not user cancel)
					error = `Request timed out after ${FETCH_TIMEOUT_MS / 1000}s. The exchange may have too many instruments.`;
				}
				// User-triggered cancel: component is already unmounting via handleCancel → onClose()
			} else {
				error = e instanceof Error ? e.message : 'Failed to load instruments';
			}
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadInstruments();
		// Abort in-flight fetch when the modal unmounts (treat as user cancel to avoid stale error)
		return () => {
			userCancelled = true;
			abortController?.abort();
		};
	});

	// ── Open full instrument detail ────────────────────────────
	// We already have the complete instrument object from the exchange load —
	// no second API call needed; just show it directly.
	function openInstrument(instrument: Record<string, any>) {
		selectedInstrument = instrument;
	}

	// ── CSV export ─────────────────────────────────────────────
	function exportCsv() {
		if (filteredInstruments.length === 0) return;
		exporting = true;

		try {
			const cols = displayColumns;

			// Header row
			const header = cols.map(escCsv).join(',');

			// Data rows — export ALL filtered instruments (not just current page)
			const rows = filteredInstruments.map((inst) =>
				cols.map((col) => escCsv(String(inst[col] ?? ''))).join(',')
			);

			const csv = [header, ...rows].join('\r\n');
			const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
			const url = URL.createObjectURL(blob);

			const filename = `failed-${columnName}-${exchange}-${new Date().toISOString().slice(0, 10)}.csv`;

			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			a.click();
			URL.revokeObjectURL(url);
		} finally {
			exporting = false;
		}
	}

	function escCsv(v: string): string {
		// Wrap in quotes if the value contains a comma, newline, or double-quote
		if (v.includes(',') || v.includes('\n') || v.includes('"')) {
			return `"${v.replace(/"/g, '""')}"`;
		}
		return v;
	}

	// ── Navigation helpers ─────────────────────────────────────
	function goTo(page: number) {
		currentPage = Math.max(1, Math.min(page, totalPages));
	}

	/** Compact page number list with ellipsis gaps */
	const pageNumbers = $derived.by((): (number | '…')[] => {
		const total = totalPages;
		if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
		const cur = currentPage;
		const pages: (number | '…')[] = [1];
		if (cur > 3) pages.push('…');
		for (let p = Math.max(2, cur - 1); p <= Math.min(total - 1, cur + 1); p++) pages.push(p);
		if (cur < total - 2) pages.push('…');
		pages.push(total);
		return pages;
	});

	function handleOverlayKey(e: KeyboardEvent) {
		if (e.key === 'Escape' && !selectedInstrument) onClose();
	}

	function safeFixed(v: number | null | undefined, d = 1) {
		return v != null && !isNaN(v) ? v.toFixed(d) : '0';
	}

	const startRow = $derived((currentPage - 1) * pageSize + 1);
	const endRow = $derived(Math.min(currentPage * pageSize, filteredInstruments.length));
</script>

<!-- Nested instrument detail -->
{#if selectedInstrument}
	<InstrumentDetailsModal
		open={true}
		instrument={selectedInstrument}
		onClose={() => (selectedInstrument = null)}
	/>
{/if}

<!-- Rule YAML viewer for the column -->
{#if showRuleYaml}
	<RuleYamlModal
		rule={{ RuleName: columnName, RuleType: 'column', RuleLevel: '', RuleSource: '' }}
		exchange={exchange}
		productType={productType}
		onClose={() => (showRuleYaml = false)}
	/>
{/if}

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
	class="overlay"
	role="dialog"
	aria-modal="true"
	aria-label="Failed instruments"
	tabindex="-1"
	onclick={!selectedInstrument ? onClose : undefined}
	onkeydown={handleOverlayKey}
>
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div class="modal" role="document" onclick={(e) => e.stopPropagation()} onkeydown={() => {}}>

		<!-- ── Header ─────────────────────────────────────────── -->
		<div class="modal-header">
			<div class="header-left">
				<h2>Failed Instruments</h2>
				<div class="header-meta">
					<button
						class="badge col clickable"
						onclick={() => (showRuleYaml = true)}
						type="button"
						title="Click to view rule YAML"
					>
						{columnName}
						<svg class="rule-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
						</svg>
					</button>
					<span class="badge type">{expectationType}</span>
					<span class="badge exchange">{exchange}</span>
					<span class="badge product">{productType}</span>
				</div>
			</div>
			<div class="header-actions">
				{#if !loading && failedInstruments.length > 0}
					<button class="export-btn" onclick={exportCsv} disabled={exporting} type="button">
						{#if exporting}
							<span class="spinner-sm"></span>
						{:else}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
							</svg>
						{/if}
						Export CSV
					</button>
				{/if}
				<button class="close-btn" onclick={onClose} type="button" aria-label="Close">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
		</div>

		<!-- ── Stats strip ────────────────────────────────────── -->
		<div class="stats-strip">
			<div class="stat">
				<span class="stat-label">Unexpected Count</span>
				<span class="stat-value fail">{unexpectedCount}</span>
			</div>
			<div class="stat">
				<span class="stat-label">Unexpected %</span>
				<span class="stat-value fail">{safeFixed(unexpectedPercent)}%</span>
			</div>
			{#if hasMissingValues}
				<div class="stat">
					<span class="stat-label">Missing Count</span>
					<span class="stat-value warn">{missingCount}</span>
				</div>
			{/if}
			{#if !loading}
				<div class="stat">
					<span class="stat-label">Instruments Found</span>
					<span class="stat-value">{failedInstruments.length.toLocaleString()}</span>
				</div>
				{#if searchQuery && filteredInstruments.length !== failedInstruments.length}
					<div class="stat">
						<span class="stat-label">Filtered</span>
						<span class="stat-value">{filteredInstruments.length.toLocaleString()}</span>
					</div>
				{/if}
			{/if}
		</div>

		<!-- ── Unexpected values ──────────────────────────────── -->
		{#if unexpectedValues.length > 0}
			<div class="values-strip">
				<span class="values-label">Unexpected values:</span>
				{#each unexpectedValues as item}
					<span class="value-chip">
						<code>{item.value || '(empty)'}</code>
						<span class="value-count">{item.count}×</span>
					</span>
				{/each}
			</div>
		{/if}

		<!-- ── Uniqueness notice ──────────────────────────────── -->
		{#if isUniqueExpectation && unexpectedValues.length > 0}
			<div class="notice-strip">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10" />
					<path stroke-linecap="round" d="M12 8v4M12 16h.01" />
				</svg>
				<span>
					Uniqueness violation — the {unexpectedValues.length === 1 ? 'value below appears' : 'values below appear'} in multiple records.
					All duplicate rows are shown.
				</span>
			</div>
		{/if}

		<!-- ── Body ───────────────────────────────────────────── -->
		<div class="modal-body">
			{#if loading}
				<div class="state-msg">
					<span class="spinner"></span>
					<div>
						<p>Loading instruments for <strong>{exchange}</strong> ({normalisedProductType})…</p>
						<p class="hint">Filtering by {unexpectedValueStrings.length} value{unexpectedValueStrings.length !== 1 ? 's' : ''}. Large exchanges may take a moment.</p>
					<button class="retry-btn cancel-btn" onclick={handleCancel} type="button">
						✕ Cancel
					</button>
					</div>
				</div>
			{:else if error}
				<div class="state-msg error">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="10" />
						<path stroke-linecap="round" d="M12 8v4M12 16h.01" />
					</svg>
					<div>
						<p>{error}</p>
						<button class="retry-btn" onclick={loadInstruments} type="button">
							↺ Retry
						</button>
					</div>
				</div>
			{:else if noDetailAvailable}
				<div class="state-msg muted">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="10" />
						<path stroke-linecap="round" d="M12 8v4M12 16h.01" />
					</svg>
					<div>
						<p>No unexpected-value details stored for this expectation.</p>
						<p class="hint">
							{unexpectedCount} record{unexpectedCount !== 1 ? 's' : ''} failed, but GE did not
							return partial unexpected values for this check type.
						</p>
					</div>
				</div>
		{:else if failedInstruments.length === 0}
			<div class="state-msg muted">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="10" />
					<path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
				</svg>
				<div>
					<p>No instruments found for {unexpectedValues.length > 0 ? `value${unexpectedValues.length > 1 ? 's' : ''} [${unexpectedValues.map(v => v.value || '(empty)').join(', ')}]` : 'these values'}.</p>
					<p class="hint">
						The data may have been corrected since this validation ran.
					</p>
				</div>
			</div>
			{:else}
				<!-- ── Toolbar ─────────────────────────────────── -->
				<div class="toolbar">
					<div class="search-wrap">
						<svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<circle cx="11" cy="11" r="8" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35" />
						</svg>
						<input
							class="search-input"
							type="text"
							bind:value={searchQuery}
							placeholder="Search MasterId, RIC, Symbol…"
							aria-label="Search instruments"
						/>
						{#if searchQuery}
							<button class="clear-search" onclick={() => (searchQuery = '')} type="button" aria-label="Clear search">
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						{/if}
					</div>

					<div class="toolbar-right">
						<span class="row-range">
							{startRow.toLocaleString()}–{endRow.toLocaleString()} of {filteredInstruments.length.toLocaleString()}
						</span>
						<label class="page-size-label">
							Rows
							<select class="page-size-select" bind:value={pageSize}>
								{#each PAGE_SIZES as ps}
									<option value={ps}>{ps}</option>
								{/each}
							</select>
						</label>
					</div>
				</div>

				<!-- ── Table ─────────────────────────────────── -->
				<div class="table-wrap">
					<table>
						<thead>
							<tr>
								{#each displayColumns as col}
									<th class={col === columnName ? 'col-highlight' : ''}>{col}</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each pageInstruments as inst, rowIdx (`${rowIdx}-${inst.MasterId ?? JSON.stringify(inst)}`)}
								<tr
									class="inst-row"
									onclick={() => openInstrument(inst)}
									role="button"
									tabindex="0"
									onkeydown={(e) => {
										if (e.key === 'Enter' || e.key === ' ') openInstrument(inst);
									}}
									title="Click to view full instrument details"
								>
									{#each displayColumns as col}
										<td class="{col === columnName ? 'cell-fail col-highlight' : col === 'MasterId' ? 'cell-master-id' : ''}">
											{inst[col] ?? '—'}
										</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- ── Pagination controls ───────────────────── -->
				{#if totalPages > 1}
					<div class="pagination">
						<button
							class="page-btn nav"
							onclick={() => goTo(currentPage - 1)}
							disabled={currentPage === 1}
							type="button"
							aria-label="Previous page"
						>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
							</svg>
						</button>

						{#each pageNumbers as p}
							{#if p === '…'}
								<span class="page-ellipsis">…</span>
							{:else}
								<button
									class="page-btn {currentPage === p ? 'active' : ''}"
									onclick={() => goTo(p)}
									type="button"
									aria-label="Page {p}"
									aria-current={currentPage === p ? 'page' : undefined}
								>
									{p}
								</button>
							{/if}
						{/each}

						<button
							class="page-btn nav"
							onclick={() => goTo(currentPage + 1)}
							disabled={currentPage === totalPages}
							type="button"
							aria-label="Next page"
						>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
							</svg>
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<style>
	/* ── Overlay & modal shell ────────────────────────────────── */
	.overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10000;
		padding: 1rem;
	}

	.modal {
		background: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		width: min(960px, 95vw);
		max-height: 90vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 25px 50px rgba(0, 0, 0, 0.7);
		overflow: hidden;
	}

	/* ── Header ───────────────────────────────────────────────── */
	.modal-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.875rem 1.25rem;
		border-bottom: 1px solid #1f2937;
		flex-shrink: 0;
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.modal-header h2 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #fff;
	}

	.header-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}

	.badge {
		padding: 0.15rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.6875rem;
		font-weight: 500;
	}

	.badge.col {
		background: rgba(239, 68, 68, 0.15);
		color: #f87171;
		border: 1px solid rgba(239, 68, 68, 0.3);
		font-family: monospace;
	}

	.badge.col.clickable {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		cursor: pointer;
		transition: background 0.15s, border-color 0.15s;
	}

	.badge.col.clickable:hover {
		background: rgba(239, 68, 68, 0.28);
		border-color: rgba(239, 68, 68, 0.6);
	}

	.rule-icon {
		width: 0.75rem;
		height: 0.75rem;
		opacity: 0.7;
		flex-shrink: 0;
	}

	.badge.type {
		background: #1f2937;
		color: #9ca3af;
		border: 1px solid #374151;
		font-family: monospace;
		font-size: 0.625rem;
	}

	.badge.exchange {
		background: #1e3a5f;
		color: #60a5fa;
		border: 1px solid #1e40af;
	}

	.badge.product {
		background: #1f2937;
		color: #6b7280;
		border: 1px solid #374151;
		text-transform: uppercase;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	/* Export button */
	.export-btn {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #d1d5db;
		font-size: 0.8125rem;
		font-weight: 500;
		padding: 0.375rem 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
		white-space: nowrap;
	}

	.export-btn:hover:not(:disabled) {
		background: #374151;
		border-color: #34d399;
		color: #34d399;
	}

	.export-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.export-btn svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		cursor: pointer;
		width: 2rem;
		height: 2rem;
		padding: 0;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.close-btn:hover {
		background: #374151;
		color: #fff;
		border-color: var(--color-primary);
	}

	.close-btn svg {
		width: 1rem;
		height: 1rem;
	}

	/* ── Stats strip ──────────────────────────────────────────── */
	.stats-strip {
		display: flex;
		flex-wrap: wrap;
		gap: 1.5rem;
		padding: 0.625rem 1.25rem;
		background: #0d1117;
		border-bottom: 1px solid #1f2937;
		flex-shrink: 0;
	}

	.stat {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.stat-label {
		font-size: 0.6875rem;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.stat-value {
		font-size: 0.9375rem;
		font-weight: 700;
		color: #e5e7eb;
	}

	.stat-value.fail { color: #f87171; }
	.stat-value.warn { color: #fbbf24; }

	/* ── Values strip ─────────────────────────────────────────── */
	.values-strip {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.4rem;
		padding: 0.5rem 1.25rem;
		background: #0d1117;
		border-bottom: 1px solid #1f2937;
		flex-shrink: 0;
	}

	.values-label {
		font-size: 0.6875rem;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		white-space: nowrap;
	}

	.value-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.25);
		border-radius: 0.25rem;
		padding: 0.125rem 0.45rem;
	}

	.value-chip code {
		font-family: monospace;
		font-size: 0.75rem;
		color: #f87171;
	}

	.value-count {
		font-size: 0.6875rem;
		color: #9ca3af;
	}

	/* ── Uniqueness notice strip ──────────────────────────────── */
	.notice-strip {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1.25rem;
		background: rgba(251, 191, 36, 0.06);
		border-bottom: 1px solid rgba(251, 191, 36, 0.2);
		color: #fbbf24;
		font-size: 0.75rem;
		flex-shrink: 0;
	}

	.notice-strip svg {
		width: 0.875rem;
		height: 0.875rem;
		flex-shrink: 0;
	}

	/* ── Modal body ───────────────────────────────────────────── */
	.modal-body {
		overflow-y: auto;
		flex: 1;
		display: flex;
		flex-direction: column;
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #0d1117;
	}

	.modal-body::-webkit-scrollbar { width: 8px; }
	.modal-body::-webkit-scrollbar-track { background: #0d1117; }
	.modal-body::-webkit-scrollbar-thumb { background: var(--color-primary-dark); border-radius: 4px; }

	/* ── Toolbar (search + page size + row range) ─────────────── */
	.toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		padding: 0.375rem 0.875rem;
		border-bottom: 1px solid #1f2937;
		flex-shrink: 0;
		flex-wrap: wrap;
	}

	.search-wrap {
		position: relative;
		display: flex;
		align-items: center;
		flex: 1;
		min-width: 180px;
		max-width: 340px;
	}

	.search-icon {
		position: absolute;
		left: 0.625rem;
		width: 0.875rem;
		height: 0.875rem;
		color: #6b7280;
		pointer-events: none;
	}

	.search-input {
		width: 100%;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #e5e7eb;
		font-size: 0.75rem;
		padding: 0.3rem 2rem 0.3rem 2.1rem;
		outline: none;
		transition: border-color 0.2s;
	}

	.search-input:focus {
		border-color: var(--color-primary);
	}

	.search-input::placeholder {
		color: #6b7280;
	}

	.clear-search {
		position: absolute;
		right: 0.5rem;
		background: none;
		border: none;
		cursor: pointer;
		color: #6b7280;
		display: flex;
		padding: 0;
		transition: color 0.15s;
	}

	.clear-search:hover { color: #e5e7eb; }

	.clear-search svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	.toolbar-right {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.row-range {
		font-size: 0.75rem;
		color: #9ca3af;
		white-space: nowrap;
	}

	.page-size-label {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		color: #9ca3af;
		white-space: nowrap;
	}

	.page-size-select {
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		color: #e5e7eb;
		font-size: 0.75rem;
		padding: 0.2rem 0.4rem;
		outline: none;
		cursor: pointer;
	}

	/* ── Table ────────────────────────────────────────────────── */
	.table-wrap {
		overflow-x: auto;
		flex: 1;
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.75rem;
	}

	thead th {
		background: #1f2937;
		padding: 0.375rem 0.75rem;
		text-align: left;
		font-size: 0.625rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		white-space: nowrap;
		border-bottom: 1px solid #374151;
		position: sticky;
		top: 0;
		z-index: 1;
	}

	thead th.col-highlight {
		color: #f87171;
		background: rgba(239, 68, 68, 0.08);
	}

	.inst-row td {
		padding: 0.35rem 0.75rem;
		border-bottom: 1px solid #1a2234;
		cursor: pointer;
		transition: background 0.12s;
	}

	.inst-row:hover td { background: #1a2332; }
	.inst-row:last-child td { border-bottom: none; }

	.cell-master-id {
		font-family: monospace;
		color: var(--color-primary-light);
	}

	.cell-fail {
		color: #f87171;
	}

	td.col-highlight {
		background: rgba(239, 68, 68, 0.06);
	}

	/* ── Pagination ───────────────────────────────────────────── */
	.pagination {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
		padding: 0.375rem 0.875rem;
		border-top: 1px solid #1f2937;
		flex-shrink: 0;
		flex-wrap: wrap;
	}

	.page-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 1.75rem;
		height: 1.75rem;
		padding: 0 0.4rem;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		font-size: 0.75rem;
		cursor: pointer;
		transition: all 0.15s;
	}

	.page-btn:hover:not(:disabled):not(.active) {
		background: #374151;
		color: #e5e7eb;
		border-color: var(--color-primary);
	}

	.page-btn.active {
		background: var(--gradient-primary);
		border-color: var(--color-primary-dark);
		color: #fff;
		font-weight: 600;
	}

	.page-btn:disabled {
		opacity: 0.35;
		cursor: not-allowed;
	}

	.page-btn.nav svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	.page-ellipsis {
		color: #6b7280;
		font-size: 0.75rem;
		padding: 0 0.25rem;
		line-height: 1.75rem;
	}

	/* ── State messages ───────────────────────────────────────── */
	.state-msg {
		display: flex;
		align-items: flex-start;
		justify-content: center;
		gap: 0.875rem;
		padding: 2rem 1.5rem;
		color: #9ca3af;
		font-size: 0.8125rem;
	}

	.state-msg .spinner {
		margin-top: 0.2rem;
		flex-shrink: 0;
	}

	.state-msg.error {
		color: #f87171;
		align-items: flex-start;
		justify-content: flex-start;
	}

	.retry-btn {
		margin-top: 0.5rem;
		display: inline-flex;
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

	.retry-btn:hover {
		background: #374151;
		border-color: var(--color-primary);
		color: #fff;
	}

	.cancel-btn {
		border-color: #4b5563;
	}

	.cancel-btn:hover {
		border-color: #f87171;
		color: #f87171;
	}

	.state-msg.muted {
		color: #6b7280;
		align-items: flex-start;
		justify-content: flex-start;
	}

	.state-msg svg {
		width: 2rem;
		height: 2rem;
		flex-shrink: 0;
		color: #4b5563;
	}

	.state-msg p { margin: 0 0 0.25rem; }

	.state-msg .hint {
		font-size: 0.75rem;
		color: #4b5563;
	}

	.spinner {
		width: 1.25rem;
		height: 1.25rem;
		border: 2px solid #374151;
		border-top-color: var(--color-primary);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	.spinner-sm {
		width: 0.875rem;
		height: 0.875rem;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: #fff;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		display: inline-block;
	}

	@keyframes spin { to { transform: rotate(360deg); } }
</style>
