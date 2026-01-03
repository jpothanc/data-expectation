<script lang="ts">
	import { page } from '$app/stores';
	import ValidationTab from '$lib/components/ValidationTab.svelte';
	import InstrumentsTab from '$lib/components/InstrumentsTab.svelte';
	import RulesTab from '$lib/components/RulesTab.svelte';
	import HomeButton from '$lib/components/HomeButton.svelte';

	let activeTab = $state<'validation' | 'instruments' | 'rules'>('instruments');
	let initialExchange = $state<string | null>(null);

	// Read URL parameters on mount
	$effect(() => {
		const exchangeParam = $page.url.searchParams.get('exchange');
		const tabParam = $page.url.searchParams.get('tab');
		
		if (exchangeParam) {
			initialExchange = exchangeParam;
		}
		
		if (tabParam === 'validation') {
			activeTab = 'validation';
		}
	});

	function handleTabChange(tabId: string) {
		activeTab = tabId as 'validation' | 'instruments' | 'rules';
	}


	const tabs = [
		{ id: 'instruments', label: 'Instruments' },
		{ id: 'validation', label: 'Validation' },
		{ id: 'rules', label: 'Rules' }
	];
</script>

<div class="stocks-layout">
	<nav class="tabs-nav">
		<HomeButton size="medium" />
		{#each tabs as tab}
			<button
				class="tab-button {activeTab === tab.id ? 'active' : ''}"
				onclick={() => handleTabChange(tab.id)}
				type="button"
			>
				{tab.label}
			</button>
		{/each}
		<h1 class="header-title">Stock</h1>
	</nav>
	
	<main class="stocks-content">

	{#key activeTab}
		{#if activeTab === 'validation'}
			<ValidationTab initialExchange={initialExchange} productType="stock" />
		{:else if activeTab === 'instruments'}
			<InstrumentsTab productType="stock" />
		{:else if activeTab === 'rules'}
			<RulesTab productType="stock" />
		{/if}
	{/key}
	</main>
</div>

<style>
	:global(body) {
		background-color: #000000;
		color: #e5e7eb;
	}

	.stocks-layout {
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
	
	.stocks-content {
		max-width: 1400px;
		margin: 0 auto;
		padding: 1.5rem 2rem;
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
		
		.stocks-content {
			padding: 1rem;
		}
	}
</style>
