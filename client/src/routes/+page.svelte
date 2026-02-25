<script lang="ts">
	import { goto } from '$app/navigation';
	import ThemeSelector from '$lib/components/ui/ThemeSelector.svelte';

	function navigateTo(path: string) {
		goto(path);
	}
</script>

<div class="landing-page">
	<div class="theme-selector-wrapper">
		<ThemeSelector />
	</div>
	<div class="hero-section">
		<h1 class="main-title">Instruments GE</h1>
		<p class="subtitle">Financial Instruments Management Platform</p>
	</div>

	<div class="navigation-grid">
		<button class="nav-card" onclick={() => navigateTo('/analytics/overview')} type="button">
			<div class="card-icon">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 13a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1h-4a1 1 0 01-1-1v-6z" />
				</svg>
			</div>
			<h2 class="card-title">Dashboard</h2>
			<p class="card-description">Analytics & insights</p>
		</button>

		<button class="nav-card" onclick={() => navigateTo('/stocks')} type="button">
			<div class="card-icon">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
				</svg>
			</div>
			<h2 class="card-title">Stocks</h2>
			<p class="card-description">Stock validation</p>
		</button>

		<button class="nav-card options-card" onclick={() => navigateTo('/options')} type="button">
			<div class="card-icon">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
			</div>
			<h2 class="card-title">Options</h2>
			<p class="card-description">Options validation</p>
		</button>

		<button class="nav-card futures-card" onclick={() => navigateTo('/futures')} type="button">
			<div class="card-icon">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
			</div>
			<h2 class="card-title">Futures</h2>
			<p class="card-description">Futures validation</p>
		</button>

		<button class="nav-card multileg-card" onclick={() => navigateTo('/multileg')} type="button">
			<div class="card-icon">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
				</svg>
			</div>
			<h2 class="card-title">MultiLeg</h2>
			<p class="card-description">Multi-leg validation</p>
		</button>

		<button class="nav-card reports-card" onclick={() => navigateTo('/reports')} type="button">
			<div class="card-icon">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
				</svg>
			</div>
			<h2 class="card-title">Reports</h2>
			<p class="card-description">Historical run reports</p>
		</button>
	</div>
</div>

<style>
	:global(body) {
		background-color: #000000;
		color: #e5e7eb;
		margin: 0;
		padding: 0;
	}

	.landing-page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		background: linear-gradient(135deg, #000000 0%, #1a1a2e 100%);
		position: relative;
	}

	.theme-selector-wrapper {
		position: absolute;
		top: 1rem;
		right: 1rem;
		z-index: 10;
	}

	.hero-section {
		text-align: center;
		margin-bottom: 1.5rem;
	}

	.main-title {
		font-size: 2rem;
		font-weight: 700;
		background: var(--gradient-primary);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin-bottom: 0.25rem;
		letter-spacing: -0.02em;
	}

	.subtitle {
		font-size: 0.875rem;
		color: #9ca3af;
		font-weight: 400;
	}

	.navigation-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
		max-width: 640px;
		width: 100%;
	}

	.nav-card {
		background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
		border: 1px solid #374151;
		border-radius: 0.5rem;
		padding: 0.75rem;
		cursor: pointer;
		transition: all 0.25s ease;
		text-align: left;
		position: relative;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.nav-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 4px;
		background: var(--gradient-accent);
		transform: scaleX(0);
		transition: transform 0.3s ease;
	}

	.nav-card:hover:not(:disabled)::before {
		transform: scaleX(1);
	}

	.nav-card:hover:not(:disabled) {
		border-color: var(--color-primary-light);
		transform: translateY(-2px);
		box-shadow: 0 6px 16px var(--shadow-primary);
	}

	.nav-card:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.nav-card:disabled:hover {
		transform: none;
		border-color: #374151;
		box-shadow: none;
	}

	.card-icon {
		width: 1.25rem;
		height: 1.25rem;
		color: var(--color-primary-light);
		margin-bottom: 0.125rem;
	}

	.card-icon svg {
		width: 100%;
		height: 100%;
	}

	.nav-card:disabled .card-icon {
		color: #6b7280;
	}

	.card-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: #ffffff;
		margin: 0;
	}

	.card-description {
		font-size: 0.6875rem;
		color: #6b7280;
		margin: 0;
		line-height: 1.3;
	}

	.reports-card .card-icon {
		color: var(--color-primary-light);
	}

	.multileg-card .card-icon {
		color: var(--color-primary-light);
	}

	@media (max-width: 480px) {
		.navigation-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>
