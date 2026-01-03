<script lang="ts">
	import { formatHeaderName } from '../utils/formatters';

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
		if (value === null || value === undefined) {
			return '—';
		}
		if (typeof value === 'boolean') {
			return value ? 'Yes' : 'No';
		}
		if (typeof value === 'object') {
			return JSON.stringify(value, null, 2);
		}
		return String(value);
	}

	function getSortedKeys(obj: Record<string, any>): string[] {
		if (!obj) return [];
		const commonFields = ['RIC', 'Symbol', 'IssuerName', 'Exchange', 'SecurityType', 'TradingStatus', 'Currency', 'MasterId'];
		const keys = Object.keys(obj);
		return [
			...commonFields.filter(field => keys.includes(field)),
			...keys.filter(key => !commonFields.includes(key)).sort()
		];
	}

	$effect(() => {
		if (open && typeof window !== 'undefined') {
			window.addEventListener('keydown', handleEscape);
			document.body.style.overflow = 'hidden';
			return () => {
				window.removeEventListener('keydown', handleEscape);
				document.body.style.overflow = '';
			};
		}
	});
</script>

{#if open && instrument}
	{@const sortedKeys = getSortedKeys(instrument)}
	<div
		class="modal-backdrop"
		onclick={handleBackdropClick}
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
	>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<div class="header-left">
					<h2 id="modal-title" class="modal-title">
						{instrument.RIC || instrument.Symbol || instrument.MasterId || 'Instrument Details'}
					</h2>
					{#if instrument.Exchange}
						<span class="exchange-badge">{instrument.Exchange}</span>
					{/if}
				</div>
				<button class="close-button" onclick={onClose} type="button" aria-label="Close">
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="modal-body">
				<div class="key-value-list">
					{#each sortedKeys as key}
						<div class="key-value-item">
							<div class="key-label">{formatHeaderName(key)}</div>
							<div class="value-content">
								{#if typeof instrument[key] === 'object' && instrument[key] !== null && !Array.isArray(instrument[key])}
									<pre class="json-value">{formatValue(instrument[key])}</pre>
								{:else}
									<span class="value-text">{formatValue(instrument[key])}</span>
								{/if}
							</div>
						</div>
					{/each}
				</div>
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
		z-index: 10000;
		padding: 1rem;
		overflow-y: auto;
	}

	.modal-content {
		background-color: #1f2937;
		border-radius: 0.5rem;
		border: 1px solid #374151;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
		max-width: 800px;
		width: 100%;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.25rem 1.5rem;
		border-bottom: 1px solid #374151;
		flex-shrink: 0;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex: 1;
		min-width: 0;
	}

	.modal-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: #ffffff;
		margin: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.exchange-badge {
		display: inline-block;
		padding: 0.25rem 0.5rem;
		background-color: var(--color-primary-dark);
		color: #ffffff;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		flex-shrink: 0;
	}

	.close-button {
		background: none;
		border: none;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background-color 0.2s, color 0.2s;
		flex-shrink: 0;
	}

	.close-button:hover {
		background-color: #374151;
		color: #ffffff;
	}

	.close-button svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.modal-body {
		padding: 1.5rem;
		overflow-y: auto;
		flex: 1;
		min-height: 0;
	}

	/* Custom scrollbar styling */
	.modal-body::-webkit-scrollbar {
		width: 10px;
	}

	.modal-body::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 5px;
	}

	.modal-body::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.modal-body::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	.modal-body {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.key-value-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.key-value-item {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 1rem;
		padding: 0.75rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		transition: border-color 0.2s;
	}

	.key-value-item:hover {
		border-color: var(--color-primary-dark);
	}

	.key-label {
		font-size: 0.8125rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		word-break: break-word;
	}

	.value-content {
		font-size: 0.875rem;
		color: #e5e7eb;
		word-break: break-word;
		overflow-wrap: break-word;
	}

	.value-text {
		display: block;
		line-height: 1.5;
	}

	.json-value {
		margin: 0;
		padding: 0.5rem;
		background-color: #0f172a;
		border: 1px solid #1e293b;
		border-radius: 0.25rem;
		font-family: 'Courier New', monospace;
		font-size: 0.75rem;
		color: #cbd5e1;
		overflow-x: auto;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.empty-value {
		color: #6b7280;
		font-style: italic;
	}

	@media (max-width: 768px) {
		.modal-content {
			max-width: 100%;
			max-height: 100vh;
			border-radius: 0;
		}

		.modal-header {
			padding: 1rem;
		}

		.modal-body {
			padding: 1rem;
		}

		.key-value-item {
			grid-template-columns: 1fr;
			gap: 0.5rem;
		}

		.key-label {
			font-size: 0.75rem;
		}

		.value-content {
			font-size: 0.8125rem;
		}
	}
</style>

