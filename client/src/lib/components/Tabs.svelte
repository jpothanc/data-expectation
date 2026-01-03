<script lang="ts">
	interface Props {
		tabs: Array<{ id: string; label: string }>;
		activeTab: string;
		onTabChange: (tabId: string) => void;
	}

	let { tabs, activeTab, onTabChange }: Props = $props();
</script>

<div class="tabs">
	{#each tabs as tab}
		<button 
			class="tab {activeTab === tab.id ? 'active' : ''}"
			onclick={() => onTabChange(tab.id)}
			type="button"
		>
			{tab.label}
		</button>
	{/each}
</div>

<style>
	.tabs {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0;
		border-bottom: none;
	}

	.tab {
		padding: 0.625rem 1.25rem;
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		font-size: 0.9375rem;
		font-weight: 500;
		color: #9ca3af;
		cursor: pointer;
		transition: all 0.2s ease;
		margin-bottom: -1px;
		position: relative;
		border-radius: 0.375rem 0.375rem 0 0;
	}

	.tab:hover:not(.active) {
		color: #e5e7eb;
		background-color: rgba(31, 41, 55, 0.5);
	}

	.tab.active {
		color: var(--color-primary-light);
		border-bottom-color: var(--color-primary-light);
		font-weight: 600;
		background-color: var(--color-border);
	}

	.tab.active::before {
		content: '';
		position: absolute;
		bottom: -1px;
		left: 0;
		right: 0;
		height: 2px;
		background: var(--gradient-hover);
		opacity: 0.5;
	}
</style>

