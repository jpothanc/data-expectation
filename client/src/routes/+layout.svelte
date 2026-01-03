<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { themeStore } from '$lib/stores/theme.svelte';
	import { browser } from '$app/environment';

	let { children } = $props();

	// Initialize theme on mount
	if (browser) {
		themeStore.initialize();
		$effect(() => {
			themeStore.currentTheme; // Access to trigger reactivity
		});
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
