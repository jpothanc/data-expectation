<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		// Redirect to overview page
		goto('/analytics/overview', { replaceState: true });
	});
</script>

<div class="loading">
	<div class="spinner"></div>
	<p>Redirecting...</p>
</div>

<style>
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100vh;
		gap: 1rem;
		color: #9ca3af;
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #374151;
		border-top-color: #34d399;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
