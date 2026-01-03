<script lang="ts">
	interface Props {
		items: Array<{ label: string; value: string | number; highlight?: 'success' | 'failed' | 'info' }>;
	}

	let { items }: Props = $props();
</script>

<div class="summary-section">
	<div class="summary-card">
		{#each items as item}
			<div class="summary-item">
				<span class="summary-label">{item.label}</span>
				<span class="summary-value {item.highlight || ''}">
					{item.value}
				</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.summary-section {
		margin-top: 1rem;
		margin-bottom: 1rem;
	}

	.summary-card {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.75rem;
		padding: 1rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
	}

	.summary-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.summary-label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.summary-value {
		font-size: 1rem;
		font-weight: 600;
		color: #ffffff;
	}

	.summary-value.success {
		color: #34d399;
	}

	.summary-value.failed {
		color: #f87171;
	}

	.summary-value.info {
		color: #34d399;
	}
</style>

