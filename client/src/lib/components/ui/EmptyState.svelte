<script lang="ts">
	interface Props {
		message?: string;
	}

	let { message = 'No data available.' }: Props = $props();
</script>

<div class="empty-state">
	<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
		<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
	</svg>
	<p class="message">{message}</p>
</div>

<style>
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.625rem;
		padding: 2.5rem 1rem;
		background: rgba(55, 65, 81, 0.2);
		border: 1px dashed #374151;
		border-radius: 0.5rem;
		width: 100%;
		box-sizing: border-box;
	}

	.empty-state svg {
		width: 2rem;
		height: 2rem;
		color: #4b5563;
	}

	.message {
		margin: 0;
		font-size: 0.875rem;
		color: #6b7280;
		text-align: center;
	}
</style>
