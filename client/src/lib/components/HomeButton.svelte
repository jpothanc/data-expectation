<script lang="ts">
	import { goto } from '$app/navigation';

	interface Props {
		size?: 'small' | 'medium' | 'large';
	}

	let { size = 'medium' }: Props = $props();

	function goHome() {
		goto('/');
	}

	const sizeClasses = {
		small: { button: 'size-small', icon: 'icon-small' },
		medium: { button: 'size-medium', icon: 'icon-medium' },
		large: { button: 'size-large', icon: 'icon-large' }
	};

	const classes = sizeClasses[size];
</script>

<button
	class="home-button {classes.button}"
	onclick={goHome}
	type="button"
	title="Go to Home"
>
	<svg class="{classes.icon}" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
		<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
	</svg>
</button>

<style>
	.home-button {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		background-color: transparent;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		cursor: pointer;
		transition: all 0.2s ease;
		flex-shrink: 0;
	}

	.home-button:hover {
		background-color: #1f2937;
		border-color: var(--color-primary-light);
		color: var(--color-primary-light);
	}

	/* Size variants */
	.size-small {
		width: 2rem;
		height: 2rem;
	}

	.size-medium {
		width: 2.25rem;
		height: 2.25rem;
	}

	.size-large {
		width: 2.5rem;
		height: 2.5rem;
	}

	/* Icon sizes */
	.icon-small {
		width: 1rem;
		height: 1rem;
	}

	.icon-medium {
		width: 1.125rem;
		height: 1.125rem;
	}

	.icon-large {
		width: 1.25rem;
		height: 1.25rem;
	}
</style>

