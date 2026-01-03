<script lang="ts">
	interface Props {
		title: string;
		stats?: Array<{ label: string; value: string | number; highlight?: 'success' | 'failed' | 'default' }>;
		children?: any;
		onClick?: () => void;
	}

	let { title, stats = [], children, onClick }: Props = $props();
</script>

<div class="chart-card" class:clickable={!!onClick} onclick={onClick} role={onClick ? 'button' : undefined} tabindex={onClick ? 0 : undefined}>
	<div class="chart-header">
		<h2 class="chart-title">{title}</h2>
		{#if stats.length > 0}
			<div class="chart-stats">
				{#each stats as stat}
					<span class="stat-item">
						<span class="stat-label {stat.highlight || 'default'}">{stat.label}:</span>
						<span class="stat-value">{stat.value}</span>
					</span>
				{/each}
			</div>
		{/if}
	</div>
	<div class="chart-content">
		{@render children()}
	</div>
</div>

<style>
	.chart-card {
		background: linear-gradient(145deg, #111827 0%, #0f172a 100%);
		border: 1px solid rgba(55, 65, 81, 0.6);
		border-radius: 0.375rem;
		padding: 0.625rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: 0 1px 3px -1px rgba(0, 0, 0, 0.3), 0 1px 2px -1px rgba(0, 0, 0, 0.2);
		position: relative;
		overflow: visible;
		min-width: 0;
	}

	.chart-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: var(--gradient-hover);
		opacity: 0;
		transition: opacity 0.3s;
	}

	.chart-card.clickable {
		cursor: pointer;
	}

	.chart-card.clickable:hover {
		border-color: var(--color-border-strong);
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
		transform: translateY(-2px);
	}

	.chart-card:not(.clickable):hover {
		border-color: var(--color-border-strong);
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
		transform: translateY(-2px);
	}

	.chart-card.clickable:active {
		transform: translateY(0);
	}

	.chart-card.clickable:focus {
		outline: 2px solid var(--color-border-strong);
		outline-offset: 2px;
	}

	.chart-card:hover::before {
		opacity: 1;
	}

	.chart-header {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.chart-title {
		margin: 0;
		font-size: 0.75rem;
		font-weight: 600;
		color: #ffffff;
		letter-spacing: -0.01em;
	}

	.chart-stats {
		display: flex;
		gap: 0.375rem;
		flex-wrap: wrap;
	}

	.stat-item {
		display: flex;
		gap: 0.25rem;
		align-items: center;
		padding: 0.1rem 0.3rem;
		background: rgba(31, 41, 55, 0.5);
		border-radius: 0.2rem;
		border: 1px solid rgba(55, 65, 81, 0.5);
	}

	.stat-label {
		font-size: 0.5625rem;
		color: #9ca3af;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.stat-label.success {
		color: #34d399;
	}

	.stat-label.failed {
		color: #f87171;
	}

	.stat-value {
		font-size: 0.6875rem;
		font-weight: 700;
		color: #ffffff;
		font-variant-numeric: tabular-nums;
	}

	.chart-content {
		flex: 1;
		min-height: 0;
		width: 100%;
		position: relative;
		overflow: visible;
	}
</style>

