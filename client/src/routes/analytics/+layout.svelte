<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import HomeButton from '$lib/components/ui/HomeButton.svelte';
	
	let { children } = $props();

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
		<span class="nav-divider"></span>
		{#each tabs as tab}
			<button
				class="tab-link {activeTab === tab.id ? 'active' : ''}"
				onclick={() => navigateToTab(tab.path)}
				type="button"
			>
				{tab.label}
			</button>
		{/each}
		<h1 class="header-title">{pageTitle}</h1>
	</nav>

	<main class="analytics-content">
		{@render children()}
	</main>
</div>

<style>
	.analytics-layout {
		min-height: 100vh;
		background: linear-gradient(180deg, #000000 0%, #0a0a0f 100%);
	}

	.tabs-nav {
		display: flex;
		align-items: stretch;
		height: 42px;
		padding: 0 1.5rem;
		background-color: #111827;
		border-bottom: 1px solid #1f2937;
		gap: 0;
	}

	.tabs-nav :global(.home-button) {
		align-self: center;
		flex-shrink: 0;
	}

	.nav-divider {
		width: 1px;
		background: #1f2937;
		margin: 8px 0.75rem 8px 0.75rem;
		flex-shrink: 0;
	}

	.header-title {
		margin: 0 0 0 auto;
		align-self: center;
		font-size: 0.875rem;
		font-weight: 500;
		color: #6b7280;
		letter-spacing: 0;
		padding-left: 1rem;
		white-space: nowrap;
	}

	.tab-link {
		position: relative;
		background: transparent;
		border: none;
		padding: 0 0.875rem;
		color: #6b7280;
		font-size: 0.8125rem;
		font-weight: 500;
		cursor: pointer;
		transition: color 0.15s;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.tab-link:hover {
		color: #d1d5db;
	}

	.tab-link.active {
		color: #fff;
	}

	.tab-link.active::after {
		content: '';
		position: absolute;
		bottom: 0;
		left: 0.25rem;
		right: 0.25rem;
		height: 2px;
		background: var(--gradient-primary);
		border-radius: 2px 2px 0 0;
	}

	.analytics-content {
		padding: 0;
	}

	@media (max-width: 768px) {
		.tabs-nav {
			padding: 0 1rem;
			height: auto;
			flex-wrap: wrap;
			min-height: 42px;
		}

		.tab-link {
			font-size: 0.75rem;
			padding: 0.625rem 0.625rem;
		}

		.header-title {
			display: none;
		}
	}
</style>

