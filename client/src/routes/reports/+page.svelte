<script lang="ts">
	import {
		getRunSessionsByRegionDate,
		getValidationResultsByRegionDate,
		getExcelReportUrl
	} from '$lib/services/api';
	import type { ExchangeValidationResult, PassedExchangeRun, RunSession } from '$lib/services/api';
	import HomeButton from '$lib/components/HomeButton.svelte';
	import ReportFilters from '$lib/components/reports/ReportFilters.svelte';
	import RunSessionPicker from '$lib/components/reports/RunSessionPicker.svelte';
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
	</header>

	<div class="page-body">
	<ReportFilters
		bind:region
		bind:date
		loading={anyLoading}
		hasData={hasLoaded && runs.length > 0}
		onLoad={loadReport}
		onDownload={downloadExcel}
	/>

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
	}

	.page-body {
		padding: 1.25rem 2rem 3rem;
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

	@media (max-width: 640px) {
		.page-body {
			padding: 1rem;
		}

		.page-header {
			padding: 0 1rem;
		}
	}
</style>
