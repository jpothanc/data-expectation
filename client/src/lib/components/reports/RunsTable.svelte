<script lang="ts">
	import type { ExchangeValidationResult } from '$lib/services/api';
	import RunDetailPanel from './RunDetailPanel.svelte';

	interface Props {
		runs: ExchangeValidationResult[];
		region: string;
		date: string;
	}

	let { runs, region, date }: Props = $props();

	let expandedRunId = $state<number | null>(null);

	function toggle(runId: number) {
		expandedRunId = expandedRunId === runId ? null : runId;
	}

	function fmt(ms: number) {
		return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
	}

	function fmtDate(ts: string) {
		if (!ts) return '—';
		return new Date(ts).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
	}
</script>

<section class="table-section">
	<header class="section-header">
		<h2 class="section-title">
			{region}
			<span class="separator">·</span>
			{date}
		</h2>
		<span class="run-count">{runs.length} run{runs.length !== 1 ? 's' : ''}</span>
	</header>

	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					<th>Run ID</th>
					<th>Timestamp</th>
					<th>Exchange</th>
					<th>Product</th>
					<th>Status</th>
					<th class="num">Passed</th>
					<th class="num">Failed</th>
					<th class="num">Total</th>
					<th>Duration</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				{#each runs as run (run.RunId)}
					<tr
						class="run-row {run.Success ? 'pass' : 'fail'}"
						onclick={() => toggle(run.RunId)}
						role="button"
						tabindex="0"
						onkeydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') toggle(run.RunId);
						}}
						aria-expanded={expandedRunId === run.RunId}
					>
						<td class="run-id">#{run.RunId}</td>
						<td class="ts">{fmtDate(run.RunTimestamp)}</td>
						<td class="exchange">{run.Exchange}</td>
						<td>
							<span class="product-badge">{run.ProductType}</span>
						</td>
						<td>
							{#if run.Success}
								<span class="status-badge pass">PASS</span>
							{:else}
								<span class="status-badge fail">FAIL</span>
							{/if}
						</td>
						<td class="num pass-num">{run.SuccessfulExpectations}</td>
						<td class="num fail-num">{run.FailedExpectations}</td>
						<td class="num">{run.TotalExpectations}</td>
						<td class="dur">{fmt(run.ExecutionDurationMs ?? 0)}</td>
						<td class="chevron-cell">
							<svg
								class="chevron {expandedRunId === run.RunId ? 'open' : ''}"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
							</svg>
						</td>
					</tr>

					{#if expandedRunId === run.RunId}
						<tr class="detail-row">
							<td colspan="10">
								<RunDetailPanel {run} />
							</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		</table>
	</div>
</section>

<style>
	/* ── Section wrapper ──────────────────────────────────────── */
	.table-section {
		background: #111827;
		border: 1px solid #1f2937;
		border-radius: 0.5rem;
		overflow: hidden;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid #1f2937;
	}

	.section-title {
		margin: 0;
		font-size: 0.8125rem;
		font-weight: 600;
		color: #fff;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.separator {
		color: #4b5563;
	}

	.run-count {
		font-size: 0.75rem;
		font-weight: 500;
		color: #6b7280;
		background: #1f2937;
		padding: 0.175rem 0.625rem;
		border-radius: 9999px;
		margin-left: auto;
	}

	/* ── Table ────────────────────────────────────────────────── */
	.table-wrap {
		overflow-x: auto;
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
	}

	thead th.num {
		text-align: right;
	}

	/* ── Run rows ─────────────────────────────────────────────── */
	.run-row td {
		padding: 0.4rem 0.75rem;
		border-bottom: 1px solid #1a2234;
		vertical-align: middle;
		cursor: pointer;
		transition: background 0.15s;
	}

	.run-row:hover td {
		background: #1a2332;
	}

	.run-row:last-child td {
		border-bottom: none;
	}

	/* Left border colour by pass/fail */
	.run-row.pass .run-id {
		border-left: 3px solid #10b981;
		padding-left: 0.625rem;
	}

	.run-row.fail .run-id {
		border-left: 3px solid #ef4444;
		padding-left: 0.625rem;
	}

	.run-id {
		font-family: monospace;
		color: #9ca3af;
		white-space: nowrap;
	}

	.ts {
		color: #9ca3af;
		white-space: nowrap;
		font-size: 0.6875rem;
	}

	.exchange {
		font-weight: 600;
		color: #e5e7eb;
		white-space: nowrap;
	}

	.product-badge {
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		padding: 0.1rem 0.45rem;
		font-size: 0.6875rem;
		color: #9ca3af;
		text-transform: uppercase;
	}

	.status-badge {
		display: inline-block;
		padding: 0.2rem 0.55rem;
		border-radius: 0.25rem;
		font-size: 0.6875rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	.status-badge.pass {
		background: #064e3b;
		color: #34d399;
	}

	.status-badge.fail {
		background: #450a0a;
		color: #f87171;
	}

	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.pass-num {
		color: #34d399;
	}

	.fail-num {
		color: #f87171;
	}

	.dur {
		color: #9ca3af;
		font-size: 0.6875rem;
		white-space: nowrap;
	}

	.chevron-cell {
		text-align: center;
		width: 2rem;
	}

	.chevron {
		width: 1rem;
		height: 1rem;
		color: #6b7280;
		transition: transform 0.2s;
		display: block;
		margin: 0 auto;
	}

	.chevron.open {
		transform: rotate(90deg);
	}

	/* ── Detail row ───────────────────────────────────────────── */
	.detail-row td {
		padding: 0;
		border-bottom: 1px solid #374151;
	}
</style>
