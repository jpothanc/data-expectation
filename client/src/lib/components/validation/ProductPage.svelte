<script lang="ts">
	import { page } from '$app/stores';
	import ValidationTab from '$lib/components/validation/ValidationTab.svelte';
	import InstrumentsTab from '$lib/components/validation/InstrumentsTab.svelte';
	import RulesTab from '$lib/components/validation/RulesTab.svelte';
	import HomeButton from '$lib/components/ui/HomeButton.svelte';

	interface Props {
		/** Display label shown in the nav bar header (e.g. "Stock", "Options", "Futures") */
		title: string;
	/** Product type forwarded to child tabs */
	productType: 'stock' | 'option' | 'future' | 'multileg';
	}

	let { title, productType }: Props = $props();

	type Tab = 'instruments' | 'validation' | 'rules';

	const tabs: { id: Tab; label: string }[] = [
		{ id: 'instruments', label: 'Instruments' },
		{ id: 'validation', label: 'Validation' },
		{ id: 'rules', label: 'Rules' }
	];

	let activeTab = $state<Tab>('instruments');
	let initialExchange = $state<string | null>(null);

	$effect(() => {
		const exchangeParam = $page.url.searchParams.get('exchange');
		const tabParam = $page.url.searchParams.get('tab');
		if (exchangeParam) initialExchange = exchangeParam;
		if (tabParam === 'validation') activeTab = 'validation';
	});
</script>

<div class="product-layout">
	<nav class="tabs-nav">
		<HomeButton size="medium" />
		<span class="nav-divider"></span>
		{#each tabs as tab}
			<button
				class="tab-link {activeTab === tab.id ? 'active' : ''}"
				onclick={() => (activeTab = tab.id)}
				type="button"
			>
				{tab.label}
			</button>
		{/each}
		<h1 class="header-title">{title}</h1>
	</nav>

	<main class="product-content">
		{#key activeTab}
			{#if activeTab === 'validation'}
				<ValidationTab {initialExchange} {productType} />
			{:else if activeTab === 'instruments'}
				<InstrumentsTab {productType} />
			{:else}
				<RulesTab {productType} />
			{/if}
		{/key}
	</main>
</div>

<style>
	:global(body) {
		background-color: #000000;
		color: #e5e7eb;
	}

	.product-layout {
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

	.product-content {
		max-width: 1400px;
		margin: 0 auto;
		padding: 1rem 1.5rem;
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

		.product-content {
			padding: 0.75rem 1rem;
		}
	}
</style>
