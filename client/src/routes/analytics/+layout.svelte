<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import HomeButton from '$lib/components/HomeButton.svelte';
	
	const tabs = [
		{ id: 'overview', label: 'Overview', path: '/analytics/overview', title: 'Analytics Dashboard' },
		{ id: 'trends', label: 'Trends', path: '/analytics/trends', title: 'Failure Trends' },
		{ id: 'breakdown', label: 'Regional Breakdown', path: '/analytics/breakdown', title: 'Regional Breakdown' },
		{ id: 'rules', label: 'Rule Analysis', path: '/analytics/rules', title: 'Rule Analysis' }
	];
	
	const currentPath = $derived.by(() => $page.url.pathname);
	const activeTab = $derived.by(() => {
		const path = currentPath;
		if (path === '/analytics' || path === '/analytics/' || path.startsWith('/analytics/overview')) return 'overview';
		if (path.startsWith('/analytics/trends')) return 'trends';
		if (path.startsWith('/analytics/breakdown')) return 'breakdown';
		if (path.startsWith('/analytics/rules')) return 'rules';
		return 'overview';
	});
	
	const pageTitle = $derived.by(() => {
		const tab = tabs.find(t => t.id === activeTab);
		return tab?.title || 'Analytics Dashboard';
	});
	
	function navigateToTab(tabPath: string) {
		goto(tabPath);
	}
</script>

<div class="analytics-layout">
	<nav class="tabs-nav">
		<HomeButton size="medium" />
		{#each tabs as tab}
			<button
				class="tab-button {activeTab === tab.id ? 'active' : ''}"
				onclick={() => navigateToTab(tab.path)}
				type="button"
			>
				{tab.label}
			</button>
		{/each}
		<h1 class="header-title">{pageTitle}</h1>
	</nav>
	
	<main class="analytics-content">
		<slot />
	</main>
</div>

<style>
	.analytics-layout {
		min-height: 100vh;
		background: linear-gradient(180deg, #000000 0%, #0a0a0f 100%);
	}
	
	.tabs-nav {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem 2.5rem;
		background-color: #111827;
		border-bottom: 2px solid var(--color-border);
		flex-wrap: wrap;
	}

	.tabs-nav :global(.home-button) {
		margin-right: 0.5rem;
	}
	
	.header-title {
		margin: 0;
		margin-left: auto;
		font-size: 1.25rem;
		font-weight: 600;
		color: #ffffff;
		letter-spacing: -0.01em;
		padding-left: 1rem;
	}
	
	.tab-button {
		padding: 0.625rem 1.25rem;
		background-color: transparent;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		color: #9ca3af;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
		position: relative;
	}
	
	.tab-button:hover {
		background-color: #1f2937;
		border-color: var(--color-primary-light);
		color: #e5e7eb;
	}
	
	.tab-button.active {
		background: var(--gradient-primary);
		border-color: var(--color-primary-dark);
		color: white;
		box-shadow: 0 2px 8px var(--shadow-medium);
	}
	
	.tab-button.active::after {
		content: '';
		position: absolute;
		bottom: -2px;
		left: 0;
		right: 0;
		height: 2px;
		background: var(--gradient-hover);
	}
	
	.analytics-content {
		padding: 0;
	}
	
	@media (max-width: 768px) {
		.tabs-nav {
			padding: 1rem;
		}
		
		.tab-button {
			font-size: 0.8125rem;
			padding: 0.5rem 1rem;
		}
		
		.header-title {
			font-size: 1rem;
			padding-left: 0.5rem;
		}
	}
</style>

