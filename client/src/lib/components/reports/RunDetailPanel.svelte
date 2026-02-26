<script lang="ts">
	import type { ExchangeValidationResult } from '$lib/services/api';
	import RuleYamlModal from './RuleYamlModal.svelte';
	import FailedInstrumentsModal from './FailedInstrumentsModal.svelte';

	interface Props {
		run: ExchangeValidationResult;
	}

	let { run }: Props = $props();

	type RuleApplied = ExchangeValidationResult['rules_applied'][0];
	type ExpResult = ExchangeValidationResult['expectation_results'][0];

	let selectedRule = $state<RuleApplied | null>(null);
	let selectedExpectation = $state<ExpResult | null>(null);

	/** Parse ResultDetails JSON stored by the DB run into { value, count }[] */
	function parseUnexpectedValues(exp: ExpResult): { value: string; count: number }[] {
		if (!exp.ResultDetails) return [];
		try {
			const d = JSON.parse(exp.ResultDetails);
			if (Array.isArray(d.partial_unexpected_counts) && d.partial_unexpected_counts.length > 0) {
				return d.partial_unexpected_counts.map((item: any) => ({
					value: String(item.value ?? ''),
					count: Number(item.count ?? 1)
				}));
			}
			if (Array.isArray(d.partial_unexpected_list) && d.partial_unexpected_list.length > 0) {
				const unique = [...new Set<string>(d.partial_unexpected_list.map(String))];
				return unique.map((v) => ({
					value: v,
					count: (d.partial_unexpected_list as any[]).filter((x) => String(x) === v).length
				}));
			}
		} catch {
			// unparseable
		}
		return [];
	}

	const failedExpectations = $derived(run.expectation_results.filter((e) => !e.Success));
	const passedExpectations = $derived(run.expectation_results.filter((e) => e.Success));
	const passPercent = $derived(
		run.TotalExpectations
			? Math.round((run.SuccessfulExpectations / run.TotalExpectations) * 100)
			: 0
	);

	function safeFixed(v: number | null | undefined, d = 1) {
		return v != null && !isNaN(v) ? v.toFixed(d) : '0';
	}
</script>

{#if selectedRule}
	<RuleYamlModal
		rule={selectedRule}
		exchange={run.Exchange}
		productType={run.ProductType}
		onClose={() => (selectedRule = null)}
	/>
{/if}

{#if selectedExpectation}
	<FailedInstrumentsModal
		columnName={selectedExpectation.ColumnName}
		expectationType={selectedExpectation.ExpectationType}
		unexpectedCount={selectedExpectation.UnexpectedCount ?? 0}
		unexpectedPercent={selectedExpectation.UnexpectedPercent ?? 0}
		missingCount={selectedExpectation.MissingCount ?? 0}
		unexpectedValues={parseUnexpectedValues(selectedExpectation)}
		exchange={run.Exchange}
		productType={run.ProductType}
		onClose={() => (selectedExpectation = null)}
	/>
{/if}

<div class="panel">
	<!-- Progress bar -->
	<div class="progress-row">
		<div class="progress-bar">
			<div class="progress-fill" style="width: {passPercent}%"></div>
		</div>
		<span class="progress-label">{passPercent}% expectations passed</span>
	</div>

	<!-- Rules applied -->
	{#if run.rules_applied && run.rules_applied.length > 0}
		<div class="meta-row">
			<span class="meta-label">Rules applied</span>
			<div class="tags">
				{#each run.rules_applied as rule}
					<button
						class="rule-tag"
						onclick={() => (selectedRule = rule)}
						type="button"
						title="Click to view YAML for {rule.RuleName}"
					>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
							/>
						</svg>
						{rule.RuleName}
						{#if rule.RuleType}
							<span class="rule-type">{rule.RuleType}</span>
						{/if}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Failed expectations -->
	{#if failedExpectations.length > 0}
		<div class="exp-section">
			<h4 class="exp-title failed">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10" />
					<path stroke-linecap="round" d="M15 9l-6 6M9 9l6 6" />
				</svg>
				Failed Expectations ({failedExpectations.length})
			</h4>
			<table class="exp-table">
				<thead>
					<tr>
						<th>Column</th>
						<th>Expectation Type</th>
						<th class="num">Unexpected</th>
						<th class="num">Unexpected %</th>
						<th class="num">Elements</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each failedExpectations as exp}
						<tr
							class="exp-fail exp-clickable"
							onclick={() => (selectedExpectation = exp)}
							role="button"
							tabindex="0"
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') selectedExpectation = exp;
							}}
							title="Click to view failing instruments"
						>
							<td class="col-name">{exp.ColumnName || '—'}</td>
							<td class="exp-type">{exp.ExpectationType || '—'}</td>
							<td class="num">{exp.UnexpectedCount ?? '—'}</td>
							<td class="num">{safeFixed(exp.UnexpectedPercent)}%</td>
							<td class="num">{exp.ElementCount ?? '—'}</td>
							<td class="lookup-cell">
								<span class="lookup-hint">
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<circle cx="11" cy="11" r="8" />
										<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35" />
									</svg>
									Instruments
								</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<!-- Passed expectations (collapsible) -->
	{#if passedExpectations.length > 0}
		<details class="passed-details">
			<summary>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4" />
					<circle cx="12" cy="12" r="10" />
				</svg>
				Passed Expectations ({passedExpectations.length})
			</summary>
			<table class="exp-table">
				<thead>
					<tr>
						<th>Column</th>
						<th>Expectation Type</th>
						<th class="num">Elements</th>
					</tr>
				</thead>
				<tbody>
					{#each passedExpectations as exp}
						<tr class="exp-pass">
							<td class="col-name">{exp.ColumnName || '—'}</td>
							<td class="exp-type">{exp.ExpectationType || '—'}</td>
							<td class="num">{exp.ElementCount ?? '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</details>
	{/if}

	{#if run.expectation_results.length === 0}
		<p class="empty">No expectation detail available for this run.</p>
	{/if}
</div>

<style>
	.panel {
		padding: 0.75rem 1.25rem 1rem;
		border-left: 3px solid var(--color-primary-dark);
		background: #0d1117;
	}

	/* ── Progress bar ─────────────────────────────────────────── */
	.progress-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.875rem;
	}

	.progress-bar {
		flex: 1;
		max-width: 280px;
		height: 6px;
		background: #1f2937;
		border-radius: 9999px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: var(--gradient-primary);
		border-radius: 9999px;
		transition: width 0.4s ease;
	}

	.progress-label {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	/* ── Rules applied row ────────────────────────────────────── */
	.meta-row {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}

	.meta-label {
		font-size: 0.6875rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: #6b7280;
		padding-top: 0.35rem;
		white-space: nowrap;
	}

	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	/* Clickable rule tag */
	.rule-tag {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		padding: 0.2rem 0.5rem;
		font-size: 0.6875rem;
		color: #d1d5db;
		cursor: pointer;
		transition: all 0.2s;
	}

	.rule-tag:hover {
		background: #374151;
		border-color: var(--color-primary);
		color: var(--color-primary-light);
	}

	.rule-tag svg {
		width: 0.875rem;
		height: 0.875rem;
		color: #6b7280;
		flex-shrink: 0;
	}

	.rule-tag:hover svg {
		color: var(--color-primary);
	}

	.rule-type {
		font-size: 0.5625rem;
		text-transform: uppercase;
		color: #6b7280;
		background: #111827;
		padding: 0.1rem 0.3rem;
		border-radius: 0.2rem;
	}

	/* ── Expectation sections ─────────────────────────────────── */
	.exp-section {
		margin-bottom: 0.875rem;
	}

	.exp-title {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		font-weight: 600;
		margin: 0 0 0.375rem;
	}

	.exp-title svg {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
	}

	.exp-title.failed {
		color: #f87171;
	}

	/* ── Sub-tables ───────────────────────────────────────────── */
	.exp-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.6875rem;
		margin-bottom: 0.375rem;
	}

	.exp-table thead th {
		background: #111827;
		padding: 0.25rem 0.5rem;
		text-align: left;
		font-size: 0.625rem;
		font-weight: 600;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		border-bottom: 1px solid #1f2937;
	}

	.exp-table thead th.num {
		text-align: right;
	}

	.exp-table tbody td {
		padding: 0.3rem 0.5rem;
		border-bottom: 1px solid #111827;
	}

	.exp-fail td {
		background: rgba(239, 68, 68, 0.05);
	}

	.exp-clickable {
		cursor: pointer;
		transition: background 0.15s;
	}

	.exp-clickable:hover td {
		background: rgba(239, 68, 68, 0.12);
	}

	.lookup-cell {
		padding: 0.375rem 0.5rem !important;
		white-space: nowrap;
	}

	.lookup-hint {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.6875rem;
		color: #6b7280;
		transition: color 0.15s;
	}

	.exp-clickable:hover .lookup-hint {
		color: var(--color-primary-light);
	}

	.lookup-hint svg {
		width: 0.75rem;
		height: 0.75rem;
	}

	.exp-pass td {
		background: rgba(16, 185, 129, 0.03);
	}

	.col-name {
		font-weight: 600;
		color: #e5e7eb;
	}

	.exp-type {
		font-family: monospace;
		font-size: 0.6875rem;
		color: #9ca3af;
	}

	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		color: #d1d5db;
		white-space: nowrap;
	}

	/* ── Passed details collapsible ───────────────────────────── */
	.passed-details {
		margin-top: 0.25rem;
	}

	.passed-details summary {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		font-weight: 600;
		color: #34d399;
		cursor: pointer;
		list-style: none;
		margin-bottom: 0.375rem;
		user-select: none;
	}

	.passed-details summary svg {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
	}

	.empty {
		font-size: 0.8125rem;
		color: #6b7280;
		font-style: italic;
		margin: 0;
	}
</style>
