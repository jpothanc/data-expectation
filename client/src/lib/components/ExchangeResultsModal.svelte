<script lang="ts">
	import type { ExchangeValidationResult, PassedExchangeRun } from '$lib/services/api';
	import ReportSummary from './reports/ReportSummary.svelte';
	import RunsTable from './reports/RunsTable.svelte';
	import PassedExchangesPanel from './reports/PassedExchangesPanel.svelte';

	interface Props {
		exchange: string;
		results: ExchangeValidationResult[];
		passedRuns: PassedExchangeRun[];
		days: number;
		onClose: () => void;
	}

	let { exchange, results, passedRuns = [], days, onClose }: Props = $props();

	let activeTab = $state<'failed' | 'passed'>('failed');
</script>

<div class="modal-overlay" onclick={onClose} role="dialog" aria-modal="true" aria-labelledby="modal-title">
	<div class="modal-content" onclick={(e) => e.stopPropagation()} role="document">
		<div class="modal-header">
			<h2 id="modal-title" class="modal-title">{exchange}</h2>
			<button
				class="close-button"
				onclick={(e) => { e.preventDefault(); e.stopPropagation(); onClose(); }}
				type="button"
				aria-label="Close"
				title="Close"
			>
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="modal-body">
			{#if results.length === 0 && passedRuns.length === 0}
				<div class="no-data">
					No validation results found for <strong>{exchange}</strong>.
				</div>
			{:else}
				<ReportSummary
					runs={results}
					{passedRuns}
					{activeTab}
					onTabChange={(t) => (activeTab = t)}
				/>

				{#if activeTab === 'failed'}
					{#if results.length > 0}
						<RunsTable runs={results} region={exchange} date="Last {days} days" />
					{:else}
						<div class="empty-state">No failed exchanges in this period.</div>
					{/if}
				{:else}
					<PassedExchangesPanel {passedRuns} />
				{/if}
			{/if}
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		inset: 0;
		background-color: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: flex-start;
		justify-content: center;
		z-index: 99999;
		padding: 2rem 1rem;
		overflow-y: auto;
	}

	.modal-content {
		background-color: #111827;
		border: 1px solid #1f2937;
		border-radius: 0.5rem;
		width: 95vw;
		max-width: 1200px;
		display: flex;
		flex-direction: column;
		box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
		min-height: 0;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		height: 42px;
		border-bottom: 1px solid #1f2937;
		background-color: #111827;
		border-radius: 0.5rem 0.5rem 0 0;
		flex-shrink: 0;
		gap: 0.75rem;
	}

	.modal-title {
		margin: 0;
		font-size: 0.875rem;
		font-weight: 500;
		color: #6b7280;
	}

	.close-button {
		background: transparent;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
		flex-shrink: 0;
		width: 1.75rem;
		height: 1.75rem;
	}

	.close-button:hover {
		background-color: #374151;
		color: #ffffff;
		border-color: #34d399;
	}

	.close-button svg {
		width: 1rem;
		height: 1rem;
	}

	.modal-body {
		padding: 1.25rem 1.5rem 2rem;
		overflow-y: auto;
		flex: 1;
	}

	.modal-body::-webkit-scrollbar {
		width: 8px;
	}

	.modal-body::-webkit-scrollbar-track {
		background: #111827;
	}

	.modal-body::-webkit-scrollbar-thumb {
		background: #374151;
		border-radius: 4px;
	}

	.modal-body::-webkit-scrollbar-thumb:hover {
		background: #4b5563;
	}

	.no-data,
	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		color: #9ca3af;
		font-size: 0.875rem;
	}

	.no-data strong {
		color: #e5e7eb;
	}

	@media (max-width: 640px) {
		.modal-overlay {
			padding: 0;
			align-items: flex-start;
		}

		.modal-content {
			width: 100vw;
			border-radius: 0;
			min-height: 100vh;
		}
	}
</style>
