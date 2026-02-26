<script lang="ts">
	interface Props {
		message?: string;
	}

	let { message = 'Loading...' }: Props = $props();
</script>

<div class="loading-state" role="status" aria-live="polite">
	<div class="spinner" aria-hidden="true"></div>
	<p class="message">{message}</p>
</div>

<style>
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		padding: 3rem 1rem;
		width: 100%;
	}

	.spinner {
		width: 2rem;
		height: 2rem;
		border: 2px solid rgba(55, 65, 81, 0.4);
		border-top-color: var(--color-primary);
		border-radius: 50%;
		animation: spin 0.75s linear infinite;
		flex-shrink: 0;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.message {
		margin: 0;
		font-size: 0.875rem;
		color: #9ca3af;
	}
</style>
