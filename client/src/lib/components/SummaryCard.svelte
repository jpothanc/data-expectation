<script lang="ts">
	interface Props {
		items: Array<{ label: string; value: string | number; highlight?: 'success' | 'failed' | 'info' }>;
	}

	let { items }: Props = $props();
</script>

<div class="summary-bar">
	{#each items as item, i}
		{#if i > 0}<span class="sep">·</span>{/if}
		<span class="item">
			<span class="lbl">{item.label}</span>
			<span class="val {item.highlight || ''}">{item.value}</span>
		</span>
	{/each}
</div>

<style>
	.summary-bar {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.25rem 0;
		padding: 0.4rem 0.75rem;
		background-color: #111827;
		border: 1px solid #1f2937;
		border-radius: 0.375rem;
		margin-bottom: 0.75rem;
		font-size: 0.8125rem;
	}

	.sep {
		color: #374151;
		padding: 0 0.625rem;
		user-select: none;
	}

	.item {
		display: inline-flex;
		align-items: baseline;
		gap: 0.375rem;
	}

	.lbl {
		font-size: 0.6875rem;
		font-weight: 500;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.val {
		font-weight: 600;
		color: #e5e7eb;
	}

	.val.success { color: #34d399; }
	.val.failed  { color: #fb923c; }
	.val.info    { color: #34d399; }
</style>

