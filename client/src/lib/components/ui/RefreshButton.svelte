<script lang="ts">
	interface Props {
		loading?: boolean;
		onClick: () => void;
		disabled?: boolean;
		title?: string;
	}

	let { loading = false, onClick, disabled = false, title = 'Refresh data' }: Props = $props();
</script>

<button
	class="refresh-button"
	onclick={onClick}
	disabled={disabled || loading}
	type="button"
	{title}
>
	{#if loading}
		<svg class="refresh-icon spinning" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
		</svg>
	{:else}
		<svg class="refresh-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
		</svg>
	{/if}
</button>

<style>
	.refresh-button {
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #9ca3af;
		padding: 0;
		border-radius: 0.375rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		width: 2rem;
		height: 2rem;
	}

	.refresh-button:hover:not(:disabled) {
		background-color: var(--color-primary-dark);
		border-color: var(--color-primary-dark);
		color: white;
	}

	.refresh-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		background: #374151;
	}

	.refresh-icon {
		width: 1rem;
		height: 1rem;
	}

	.refresh-icon.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>

