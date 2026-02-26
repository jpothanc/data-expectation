<script lang="ts">
	import type { ExchangeValidationResult, PassedExchangeRun } from '$lib/services/api';

	interface Props {
		runs: ExchangeValidationResult[];
		passedRuns: PassedExchangeRun[];
		activeTab: 'failed' | 'passed';
		onTabChange: (tab: 'failed' | 'passed') => void;
	}

	let { runs, passedRuns, activeTab, onTabChange }: Props = $props();

	const totalRuns         = $derived(runs.length + passedRuns.length);
	const passRate          = $derived(totalRuns > 0 ? Math.round((passedRuns.length / totalRuns) * 100) : 0);
	const totalExpectations = $derived(
		runs.reduce((s, r) => s + (r.TotalExpectations ?? 0), 0) +
		passedRuns.reduce((s, r) => s + (r.TotalExpectations ?? 0), 0)
	);
	const failedExpectations = $derived(runs.reduce((s, r) => s + (r.FailedExpectations ?? 0), 0));
</script>

<div class="bar">
	<!-- Tab buttons — double as primary summary -->
	<div class="tabs">
		<button
			type="button"
			class="tab failed {activeTab === 'failed' ? 'active' : ''}"
			onclick={() => onTabChange('failed')}
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
				<circle cx="12" cy="12" r="10" />
				<path stroke-linecap="round" d="M15 9l-6 6M9 9l6 6" />
			</svg>
			<span class="tab-count">{runs.length}</span>
			<span class="tab-label">Failed</span>
		</button>

		<button
			type="button"
			class="tab passed {activeTab === 'passed' ? 'active' : ''}"
			onclick={() => onTabChange('passed')}
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
				<circle cx="12" cy="12" r="10" />
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4" />
			</svg>
			<span class="tab-count">{passedRuns.length}</span>
			<span class="tab-label">Passed</span>
		</button>
	</div>

	<div class="divider"></div>

	<!-- Compact inline stats -->
	<div class="stats">
		<span class="stat">
			<span class="stat-val">{totalRuns}</span>
			<span class="stat-lbl">exchanges</span>
		</span>
		<span class="sep">·</span>
		<span class="stat">
			<span class="stat-val rate">{passRate}%</span>
			<span class="stat-lbl">pass rate</span>
		</span>
		<span class="sep">·</span>
		<span class="stat">
			<span class="stat-val">{totalExpectations.toLocaleString()}</span>
			<span class="stat-lbl">checks</span>
		</span>
		{#if failedExpectations > 0}
			<span class="sep">·</span>
			<span class="stat">
				<span class="stat-val fail">{failedExpectations.toLocaleString()}</span>
				<span class="stat-lbl">failed checks</span>
			</span>
		{/if}
	</div>
</div>

<style>
	.bar {
		display: flex;
		align-items: center;
		gap: 0;
		background: #111827;
		border: 1px solid #1f2937;
		border-radius: 0.5rem;
		margin-bottom: 0.625rem;
		overflow: hidden;
		height: 2.25rem;
	}

	/* ── Tab buttons ──────────────────────────────────────────── */
	.tabs {
		display: flex;
		height: 100%;
	}

	.tab {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		height: 100%;
		padding: 0 0.875rem;
		border: none;
		border-right: 1px solid #1f2937;
		background: transparent;
		cursor: pointer;
		transition: background 0.15s;
		white-space: nowrap;
		color: #6b7280;
	}

	.tab:hover:not(.active) {
		background: #1f2937;
		color: #d1d5db;
	}

	.tab svg {
		width: 0.75rem;
		height: 0.75rem;
		flex-shrink: 0;
	}

	.tab-count {
		font-size: 0.875rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		line-height: 1;
	}

	.tab-label {
		font-size: 0.6875rem;
		font-weight: 500;
	}

	/* Active states */
	.tab.failed.active {
		background: rgba(239, 68, 68, 0.08);
		color: #f87171;
		border-bottom: 2px solid #f87171;
	}

	.tab.passed.active {
		background: rgba(52, 211, 153, 0.07);
		color: #34d399;
		border-bottom: 2px solid #34d399;
	}

	/* ── Divider ──────────────────────────────────────────────── */
	.divider {
		width: 1px;
		height: 60%;
		background: #1f2937;
		flex-shrink: 0;
		margin: 0 0.25rem;
	}

	/* ── Inline stats ─────────────────────────────────────────── */
	.stats {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0 1rem;
		flex-wrap: nowrap;
		overflow: hidden;
	}

	.stat {
		display: flex;
		align-items: baseline;
		gap: 0.3rem;
		white-space: nowrap;
	}

	.stat-val {
		font-size: 0.8125rem;
		font-weight: 700;
		color: #e5e7eb;
		font-variant-numeric: tabular-nums;
	}

	.stat-val.rate { color: var(--color-primary-light); }
	.stat-val.fail { color: #f87171; }

	.stat-lbl {
		font-size: 0.625rem;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.sep {
		color: #374151;
		font-size: 0.875rem;
		flex-shrink: 0;
	}

	@media (max-width: 600px) {
		.stats { display: none; }
	}
</style>
