<script lang="ts">
	import { formatHeaderName } from '../../utils/formatters';

	interface Props {
		open: boolean;
		data: Record<string, any> | null;
		onClose: () => void;
	}

	let { open, data, onClose }: Props = $props();

	function formatValue(value: any): string {
		if (value === null || value === undefined) {
			return '—';
		}
		if (typeof value === 'boolean') {
			return value ? 'Yes' : 'No';
		}
		if (typeof value === 'object' && !Array.isArray(value)) {
			return JSON.stringify(value, null, 2);
		}
		return String(value);
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	$effect(() => {
		if (open && typeof window !== 'undefined') {
			window.addEventListener('keydown', handleKeydown);
			document.body.style.overflow = 'hidden';
			return () => {
				window.removeEventListener('keydown', handleKeydown);
				document.body.style.overflow = '';
			};
		}
	});
</script>

{#if open && data}
	{@const sortedKeys = Object.keys(data).sort()}
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
						Expectation Failure Details
					</h2>
					{#if data.Region}
						<span class="region-badge">{data.Region}</span>
					{/if}
					{#if data.ProductType}
						<span class="product-type-badge">{data.ProductType}</span>
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
								{#if typeof data[key] === 'object' && data[key] !== null && !Array.isArray(data[key])}
									<pre class="json-value">{formatValue(data[key])}</pre>
								{:else}
									<span class="value-text">{formatValue(data[key])}</span>
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
		z-index: 1000;
		backdrop-filter: blur(4px);
		padding: 1rem;
	}

	.modal-content {
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.75rem;
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
		align-items: center;
		justify-content: space-between;
		padding: 1.25rem 1.5rem;
		border-bottom: 1px solid #374151;
		background-color: #1f2937;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.modal-title {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		color: #ffffff;
	}

	.region-badge,
	.product-type-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.region-badge {
		background-color: var(--color-primary-dark);
		color: #ffffff;
	}

	.product-type-badge {
		background-color: #374151;
		color: #e5e7eb;
	}

	.close-button {
		background: transparent;
		border: none;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.close-button:hover {
		background-color: #374151;
		color: #e5e7eb;
	}

	.close-button svg {
		width: 1.5rem;
		height: 1.5rem;
	}

	.modal-body {
		padding: 1.5rem;
		overflow-y: auto;
		flex: 1;
	}

	.key-value-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.key-value-item {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #374151;
	}

	.key-value-item:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.key-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.value-content {
		font-size: 0.875rem;
		color: #e5e7eb;
		word-break: break-word;
	}

	.value-text {
		display: block;
	}

	.json-value {
		margin: 0;
		padding: 0.75rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.8125rem;
		color: #e5e7eb;
		overflow-x: auto;
		white-space: pre-wrap;
		word-break: break-word;
	}

	@media (max-width: 640px) {
		.key-value-item {
			grid-template-columns: 1fr;
			gap: 0.5rem;
		}

		.modal-content {
			max-width: 100%;
			margin: 0.5rem;
		}

		.modal-header {
			padding: 1rem;
		}

		.modal-body {
			padding: 1rem;
		}
	}
</style>



