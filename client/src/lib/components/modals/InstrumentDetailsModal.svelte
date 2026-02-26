<script lang="ts">
	import { formatHeaderName } from '../../utils/formatters';

	interface Props {
		open: boolean;
		instrument: Record<string, any> | null;
		onClose: () => void;
	}

	let { open, instrument, onClose }: Props = $props();

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleEscape(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	function formatValue(value: any): string {
		if (value === null || value === undefined || value === '') return '';
		if (typeof value === 'boolean') return value ? 'Yes' : 'No';
		if (typeof value === 'object') {
			try {
				return JSON.stringify(value);
			} catch {
				return String(value);
			}
		}
		return String(value);
	}
</script>

{#if open && instrument}
	<div
		class="modal-backdrop"
		onclick={handleBackdropClick}
		onkeydown={handleEscape}
		role="dialog"
		tabindex="-1"
		aria-modal="true"
		aria-labelledby="instrument-modal-title"
	>
		<div class="modal-content">
			<div class="modal-header">
				<div class="header-left">
					<h2 id="instrument-modal-title" class="modal-title">
						Instrument Details{#if instrument.RIC} - {instrument.RIC}{/if}
					</h2>
				</div>
				<button class="close-button" onclick={onClose} type="button" aria-label="Close">
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="modal-body">
				{#if Object.keys(instrument).length > 0}
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>Field</th>
									<th>Value</th>
								</tr>
							</thead>
							<tbody>
								{#each Object.entries(instrument) as [key, value]}
									<tr>
										<td class="field-cell">{formatHeaderName(key)}</td>
										<td class="value-cell">{formatValue(value)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="no-data">No instrument details available.</p>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		max-width: 800px;
		width: 100%;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1.25rem;
		border-bottom: 1px solid #374151;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.modal-title {
		font-size: 0.95rem;
		font-weight: 600;
		color: #ffffff;
		margin: 0;
		line-height: 1.3;
	}

	.close-button {
		background: none;
		border: none;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 0.25rem;
		transition: all 0.2s;
	}

	.close-button:hover {
		background-color: #1f2937;
		color: #ffffff;
	}

	.close-button svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.modal-body {
		padding: 1rem 1.25rem 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		min-height: 0;
	}

	.table-container {
		border: 1px solid #374151;
		border-radius: 0.5rem;
		overflow: auto;
		background-color: #111827;
		max-height: 60vh;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
	}

	.data-table thead {
		background-color: #1f2937;
	}

	.data-table th {
		padding: 0.5rem 0.75rem;
		text-align: left;
		font-weight: 600;
		font-size: 0.75rem;
		color: #e5e7eb;
		border-bottom: 1px solid #4b5563;
	}

	.data-table td {
		padding: 0.5rem 0.75rem;
		border-bottom: 1px solid #374151;
		color: #e5e7eb;
		vertical-align: top;
	}

	.field-cell {
		width: 30%;
		font-weight: 500;
		color: #9ca3af;
		white-space: nowrap;
	}

	.value-cell {
		width: 70%;
	}

	.no-data {
		color: #9ca3af;
		font-size: 0.875rem;
		text-align: center;
		padding: 1rem 0;
	}

	@media (max-width: 640px) {
		.modal-content {
			max-height: 90vh;
		}
	}
</style>
