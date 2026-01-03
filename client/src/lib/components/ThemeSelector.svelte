<script lang="ts">
	import { themeStore, themes } from '../stores/theme.svelte';

	let isOpen = $state(false);

	function toggleDropdown() {
		isOpen = !isOpen;
	}

	function selectTheme(themeId: string) {
		themeStore.setTheme(themeId);
		isOpen = false;
	}

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.theme-selector')) {
			isOpen = false;
		}
	}

	$effect(() => {
		if (isOpen && typeof window !== 'undefined') {
			window.addEventListener('click', handleClickOutside);
			return () => {
				window.removeEventListener('click', handleClickOutside);
			};
		}
	});
</script>

<div class="theme-selector">
	<button class="theme-button" onclick={toggleDropdown} type="button" title="Select theme">
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="theme-icon">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
		</svg>
		<span class="theme-name">{themeStore.currentTheme.name}</span>
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="chevron-icon">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	{#if isOpen}
		<div class="theme-dropdown">
			{#each themes as theme}
				<button
					class="theme-option {themeStore.currentTheme.id === theme.id ? 'active' : ''}"
					onclick={() => selectTheme(theme.id)}
					type="button"
				>
					<div class="theme-preview" style="background: {theme.colors.gradient.primary};"></div>
					<span class="theme-label">{theme.name}</span>
					{#if themeStore.currentTheme.id === theme.id}
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="check-icon">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.theme-selector {
		position: relative;
	}

	.theme-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.375rem 0.75rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.75rem;
	}

	.theme-button:hover {
		background-color: #374151;
		border-color: var(--color-primary);
		color: var(--color-primary-light);
	}

	.theme-icon {
		width: 1rem;
		height: 1rem;
	}

	.theme-name {
		font-weight: 500;
		white-space: nowrap;
	}

	.chevron-icon {
		width: 0.875rem;
		height: 0.875rem;
		transition: transform 0.2s;
	}

	.theme-selector:has(.theme-button:hover) .chevron-icon,
	.theme-selector:has(.theme-dropdown) .chevron-icon {
		transform: rotate(180deg);
	}

	.theme-dropdown {
		position: absolute;
		top: calc(100% + 0.5rem);
		right: 0;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		padding: 0.5rem;
		min-width: 160px;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
		z-index: 1000;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.theme-option {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0.75rem;
		background-color: transparent;
		border: 1px solid transparent;
		border-radius: 0.375rem;
		color: #e5e7eb;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.8125rem;
		text-align: left;
		width: 100%;
	}

	.theme-option:hover {
		background-color: #374151;
		border-color: var(--color-border-medium);
	}

	.theme-option.active {
		background-color: rgba(31, 41, 55, 0.8);
		border-color: var(--color-primary);
		color: var(--color-primary-light);
	}

	.theme-preview {
		width: 1.25rem;
		height: 1.25rem;
		border-radius: 0.25rem;
		flex-shrink: 0;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.theme-label {
		flex: 1;
		font-weight: 500;
	}

	.check-icon {
		width: 1rem;
		height: 1rem;
		color: var(--color-primary-light);
		flex-shrink: 0;
	}
</style>

