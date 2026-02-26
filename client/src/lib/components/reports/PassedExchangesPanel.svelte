<script lang="ts">
	import type { PassedExchangeRun } from '$lib/services/api';

	interface Props {
		passedRuns: PassedExchangeRun[];
	}

	let { passedRuns }: Props = $props();

	function fmtTime(ts: string) {
		if (!ts) return '—';
		return new Date(ts).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
	}

	function fmt(ms: number) {
		return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
	}
</script>

{#if passedRuns.length === 0}
	<div class="empty">No passed exchanges for this session.</div>
{:else}
	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					<th>Exchange</th>
					<th>Product Type</th>
					<th>Run Time</th>
					<th class="num">Expectations</th>
					<th class="num">Duration</th>
				</tr>
			</thead>
			<tbody>
				{#each passedRuns as run (run.RunId)}
					<tr>
						<td class="exchange-cell">{run.Exchange}</td>
						<td class="product-cell">{run.ProductType ?? '—'}</td>
						<td class="time-cell">{fmtTime(run.RunTimestamp)}</td>
						<td class="num">{run.TotalExpectations ?? '—'}</td>
						<td class="num dur">{fmt(run.ExecutionDurationMs ?? 0)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}

<style>
	.empty {
		text-align: center;
		padding: 3rem 1rem;
		color: #6b7280;
		font-size: 0.9375rem;
	}

	.table-wrap {
		background: #0a1a0f;
		border: 1px solid #14532d;
		border-radius: 0.5rem;
		overflow: hidden;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
	}

	thead th {
		background: #0d2318;
		padding: 0.5rem 0.875rem;
		text-align: left;
		font-size: 0.6875rem;
		font-weight: 600;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		white-space: nowrap;
		border-bottom: 1px solid #14532d;
	}

	thead th.num { text-align: right; }

	tbody tr {
		border-bottom: 1px solid #0d2318;
		transition: background 0.1s;
	}

	tbody tr:last-child { border-bottom: none; }
	tbody tr:hover { background: rgba(52, 211, 153, 0.04); }

	tbody td { padding: 0.45rem 0.875rem; color: #d1d5db; }

	.exchange-cell {
		font-weight: 600;
		color: #34d399;
		font-family: monospace;
		font-size: 0.875rem;
	}

	.product-cell { color: #9ca3af; text-transform: capitalize; }
	.time-cell    { font-variant-numeric: tabular-nums; color: #9ca3af; }

	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}

	.dur { color: #6b7280; font-size: 0.75rem; }
</style>
