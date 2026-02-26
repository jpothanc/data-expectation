<script lang="ts">
	interface Props {
		message?: string | null;
	}

	let { message = 'An unexpected error occurred.' }: Props = $props();
</script>

{#if message}
	<div class="error-banner" role="alert">
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
			<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
		</svg>
		<p>{message}</p>
	</div>
{/if}

<style>
	.error-banner {
		display: flex;
		align-items: flex-start;
		gap: 0.625rem;
		padding: 0.75rem 1rem;
		background-color: rgba(127, 29, 29, 0.35);
		border: 1px solid #dc2626;
		border-radius: 0.375rem;
		color: #fca5a5;
		font-size: 0.875rem;
	}

	.error-banner svg {
		width: 1.125rem;
		height: 1.125rem;
		flex-shrink: 0;
		margin-top: 0.0625rem;
	}

	.error-banner p {
		margin: 0;
		line-height: 1.5;
	}
</style>
