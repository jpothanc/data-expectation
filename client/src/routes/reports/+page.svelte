<script lang="ts">
	import {
		getRunSessionsByRegionDate,
		getValidationResultsByRegionDate,
		getExcelReportUrl
	} from '$lib/services/api';
	import type { ExchangeValidationResult, PassedExchangeRun, RunSession } from '$lib/services/api';
	import HomeButton from '$lib/components/ui/HomeButton.svelte';
	import RunSessionPicker from '$lib/components/reports/RunSessionPicker.svelte';

	const REGIONS = ['APAC', 'EMEA', 'US'];
	const TODAY = new Date().toISOString().slice(0, 10);
	import ReportSummary from '$lib/components/reports/ReportSummary.svelte';
	import PassedExchangesPanel from '$lib/components/reports/PassedExchangesPanel.svelte';
	import RunsTable from '$lib/components/reports/RunsTable.svelte';

	let region = $state('APAC');
	let date   = $state(new Date().toISOString().slice(0, 10));

	let loading        = $state(false);
	let loadingSession = $state(false);
	let error          = $state<string | null>(null);

	let sessions        = $state<RunSession[]>([]);
	let selectedSession = $state('');
	let runs            = $state<ExchangeValidationResult[]>([]);
	let passedRuns      = $state<PassedExchangeRun[]>([]);
	let hasLoaded       = $state(false);
	let activeTab       = $state<'failed' | 'passed'>('failed');

	// ── Excel download ────────────────────────────────────────────
	function downloadExcel() {
		const url = getExcelReportUrl(region.toLowerCase(), date, 90);
		const a = document.createElement('a');
		a.href = url;
		a.download = `validation_report_${region.toUpperCase()}_${date}.xlsx`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
	}

	// ── Load runs for the currently selected session ───────────────
	async function loadRunsForSession(sessionTime: string) {
		if (loadingSession) return;
		selectedSession = sessionTime;
		loadingSession  = true;
		activeTab       = 'failed';
		error  = null;
		runs   = [];

		try {
			const resp = await getValidationResultsByRegionDate(
				region.toLowerCase(),
				date,
				90,
				undefined,
				sessionTime
			);
			runs       = resp.runs        ?? [];
			passedRuns = resp.passed_runs ?? [];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load runs';
		} finally {
			loadingSession = false;
		}
	}

	// ── Primary "Load Report" action ───────────────────────────────
	// 1. Fetch the lightweight session list (fast, no joins).
	// 2. Auto-select the most-recent session.
	// 3. Load runs for that session.
	async function loadReport() {
		if (loading) return;
		loading  = true;
		error    = null;
		sessions    = [];
		runs        = [];
		passedRuns  = [];

		try {
			const sessionResp = await getRunSessionsByRegionDate(region.toLowerCase(), date, 90);
			sessions = sessionResp.sessions ?? [];
			hasLoaded = true;

			if (sessions.length === 0) return;

			// Auto-select most-recent session (index 0 — server orders DESC)
			await loadRunsForSession(sessions[0].session_time);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load report';
			hasLoaded = true;
		} finally {
			loading = false;
		}
	}

	const anyLoading = $derived(loading || loadingSession);
</script>

<div class="page">
	<header class="page-header">
		<HomeButton size="medium" />
		<span class="header-divider"></span>
		<h1 class="page-title">Validation Reports</h1>
		<div class="header-spacer"></div>
		<div class="header-controls">
			<select bind:value={region} title="Region" aria-label="Region">
				{#each REGIONS as r}
					<option value={r}>{r}</option>
				{/each}
			</select>
			<input
				type="date"
				bind:value={date}
				max={TODAY}
				title="Date"
				aria-label="Date"
			/>
			<button class="load-btn" onclick={loadReport} disabled={anyLoading} type="button">
				{#if anyLoading}
					<span class="spinner"></span> Loading…
				{:else}
					Load Report
				{/if}
			</button>
			{#if hasLoaded && runs.length > 0}
				<button class="download-btn" onclick={downloadExcel} disabled={anyLoading} type="button" title="Export Excel">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
						<path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
					</svg>
					Export
				</button>
			{/if}
		</div>
	</header>

	<div class="page-body">
	{#if error}
		<div class="error-banner">{error}</div>
	{/if}

	{#if sessions.length > 0}
		<RunSessionPicker
			{sessions}
			{selectedSession}
			loading={loadingSession}
			onSelect={loadRunsForSession}
		/>
	{/if}

	{#if hasLoaded && !anyLoading}
		<ReportSummary {runs} {passedRuns} {activeTab} onTabChange={(t) => (activeTab = t)} />

		{#if runs.length === 0 && passedRuns.length === 0}
			<div class="empty-state">
				No runs found for <strong>{region}</strong> on <strong>{date}</strong>
				{#if selectedSession}at this time{/if}.
			</div>
		{:else if activeTab === 'failed'}
			{#if runs.length > 0}
				<RunsTable {runs} {region} {date} />
			{:else}
				<div class="empty-state">
					No failed exchanges for <strong>{region}</strong> on <strong>{date}</strong>
					{#if selectedSession}at this time{/if}.
				</div>
			{/if}
		{:else}
			<PassedExchangesPanel {passedRuns} />
		{/if}
	{/if}

	{#if !hasLoaded && !anyLoading}
		<div class="prompt">
			Select a region and date, then click <strong>Load Report</strong>.
		</div>
	{/if}
	</div>
</div>

<style>
	.page {
		min-height: 100vh;
		background: linear-gradient(180deg, #000000 0%, #0a0a0f 100%);
		color: #e5e7eb;
	}

	/* ── Header ───────────────────────────────────────────────── */
	.page-header {
		display: flex;
		align-items: center;
		height: 42px;
		padding: 0 1.5rem;
		background-color: #111827;
		border-bottom: 1px solid #1f2937;
		gap: 0;
	}

	.page-header :global(.home-button) {
		flex-shrink: 0;
		align-self: center;
	}

	.header-divider {
		width: 1px;
		background: #1f2937;
		height: 18px;
		margin: 0 0.75rem;
		flex-shrink: 0;
	}

	.page-title {
		margin: 0;
		font-size: 0.875rem;
		font-weight: 500;
		color: #6b7280;
		white-space: nowrap;
	}

	.header-spacer {
		flex: 1;
	}

	.header-controls {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		flex-shrink: 0;
	}

	.header-controls select,
	.header-controls input[type='date'] {
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #e5e7eb;
		padding: 0 0.625rem;
		font-size: 0.75rem;
		height: 1.875rem;
		outline: none;
		transition: border-color 0.15s;
		color-scheme: dark;
		box-sizing: border-box;
	}

	.header-controls select {
		min-width: 80px;
	}

	.header-controls input[type='date'] {
		min-width: 120px;
	}

	.header-controls select:focus,
	.header-controls input[type='date']:focus {
		border-color: var(--color-primary);
	}

	.load-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		background: var(--gradient-primary);
		border: none;
		border-radius: 0.375rem;
		color: #fff;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0 0.875rem;
		height: 1.875rem;
		cursor: pointer;
		transition: opacity 0.2s;
		white-space: nowrap;
	}

	.load-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.download-btn {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		background: #14532d;
		border: 1px solid #166534;
		border-radius: 0.375rem;
		color: #86efac;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0 0.75rem;
		height: 1.875rem;
		cursor: pointer;
		transition: background 0.2s, border-color 0.2s;
		white-space: nowrap;
	}

	.download-btn:hover:not(:disabled) {
		background: #166534;
		border-color: #15803d;
	}

	.download-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.spinner {
		width: 0.75rem;
		height: 0.75rem;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: #fff;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
		display: inline-block;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.page-body {
		padding: 1rem 2rem 3rem;
	}

	/* ── Error banner ─────────────────────────────────────────── */
	.error-banner {
		background: #450a0a;
		border: 1px solid #7f1d1d;
		border-radius: 0.375rem;
		color: #fca5a5;
		padding: 0.75rem 1rem;
		font-size: 0.875rem;
		margin-bottom: 1rem;
	}

	/* ── Empty / prompt states ────────────────────────────────── */
	.empty-state,
	.prompt {
		text-align: center;
		padding: 3rem 1rem;
		color: #6b7280;
		font-size: 0.9375rem;
	}

	.empty-state strong,
	.prompt strong {
		color: var(--color-primary-light);
	}

	@media (max-width: 768px) {
		.page-header {
			padding: 0 1rem;
			height: auto;
			min-height: 42px;
			flex-wrap: wrap;
			padding-top: 0.375rem;
			padding-bottom: 0.375rem;
			gap: 0.5rem;
		}

		.header-spacer {
			display: none;
		}

		.header-controls {
			width: 100%;
			flex-wrap: wrap;
		}

		.page-body {
			padding: 1rem;
		}
	}
</style>
