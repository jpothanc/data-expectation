<script lang="ts">
	import type { ExchangeValidationResult } from '../services/api';

	interface Props {
		isOpen: boolean;
		title: string;
		results: ExchangeValidationResult[];
		loading?: boolean;
		error?: string | null;
		onClose: () => void;
	}

	let { isOpen, title, results, loading = false, error = null, onClose }: Props = $props();

	// State for collapsible sections
	let expandedRuns = $state<Set<number>>(new Set());
	let showOnlyFailed = $state(false);
	let searchTerm = $state('');

	function formatDate(dateString: string): string {
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		} catch {
			return dateString;
		}
	}

	function parseResultDetails(resultDetails: string | null): any {
		if (!resultDetails) return null;
		try {
			return JSON.parse(resultDetails);
		} catch {
			return null;
		}
	}

	function toggleRun(index: number) {
		const newExpanded = new Set(expandedRuns);
		if (newExpanded.has(index)) {
			newExpanded.delete(index);
		} else {
			newExpanded.add(index);
		}
		expandedRuns = newExpanded;
	}

	const filteredResults = $derived.by(() => {
		let filtered = results;
		
		if (showOnlyFailed) {
			filtered = filtered.filter(run => !run.Success);
		}
		
		if (searchTerm.trim()) {
			const term = searchTerm.toLowerCase();
			filtered = filtered.filter(run => 
				run.Exchange?.toLowerCase().includes(term) ||
				run.ProductType?.toLowerCase().includes(term) ||
				run.RunTimestamp?.toLowerCase().includes(term)
			);
		}
		
		return filtered;
	});

	const summary = $derived.by(() => {
		const total = results.length;
		const successful = results.filter(r => r.Success).length;
		const failed = total - successful;
		return { total, successful, failed };
	});

	function handleBackdropClick(e: MouseEvent) {
		// Only close if clicking directly on the backdrop, not on child elements
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleBackdropMouseDown(e: MouseEvent) {
		// Prevent backdrop from interfering with panel interactions
		if (e.target === e.currentTarget) {
			e.preventDefault();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	$effect(() => {
		if (isOpen && typeof window !== 'undefined') {
			window.addEventListener('keydown', handleKeydown);
			document.body.style.overflow = 'hidden';
			return () => {
				window.removeEventListener('keydown', handleKeydown);
				document.body.style.overflow = '';
			};
		}
	});
</script>

{#if isOpen}
	<div class="panel-backdrop" onclick={handleBackdropClick} onmousedown={handleBackdropMouseDown} role="dialog" aria-modal="true">
		<div class="panel-container" onclick={(e) => e.stopPropagation()} onmousedown={(e) => e.stopPropagation()}>
			<div class="panel-header">
				<h2 class="panel-title">{title}</h2>
				<button class="close-button" onclick={onClose} type="button" aria-label="Close">
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<div class="panel-body">
				{#if loading}
					<div class="loading-state">
						<div class="spinner"></div>
						<p>Loading error details...</p>
					</div>
				{:else if error}
					<div class="error-state">
						<h3>Error</h3>
						<p>{error}</p>
					</div>
				{:else if results.length === 0}
					<div class="no-data-state">
						<p>No error details found</p>
					</div>
				{:else}
					<!-- Summary Stats -->
					<div class="summary-stats">
						<span class="stat-badge success">{summary.successful} Passed</span>
						<span class="stat-badge failed">{summary.failed} Failed</span>
						<span class="stat-badge">{summary.total} Total</span>
					</div>

					<!-- Filters -->
					<div class="filters">
						<label class="filter-checkbox">
							<input type="checkbox" bind:checked={showOnlyFailed} />
							<span>Show only failed runs</span>
						</label>
						<input
							type="text"
							class="search-input"
							placeholder="Search..."
							bind:value={searchTerm}
						/>
					</div>

					<!-- Results List -->
					<div class="results-list">
						{#each filteredResults as run, index}
							{@const isExpanded = expandedRuns.has(index)}
							{@const hasFailures = run.FailedExpectations > 0}
							<div class="result-item {hasFailures ? 'has-failures' : ''}">
								<div class="result-header" onclick={() => toggleRun(index)}>
									<div class="result-info">
										<span class="result-exchange">{run.Exchange}</span>
										<span class="result-product">{run.ProductType}</span>
										<span class="result-date">{formatDate(run.RunTimestamp || '')}</span>
									</div>
									<div class="result-status">
										{#if run.Success}
											<span class="status-badge success">Passed</span>
										{:else}
											<span class="status-badge failed">Failed</span>
										{/if}
										<svg 
											class="expand-icon {isExpanded ? 'expanded' : ''}"
											xmlns="http://www.w3.org/2000/svg" 
											fill="none" 
											viewBox="0 0 24 24" 
											stroke="currentColor"
										>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
										</svg>
									</div>
								</div>

								{#if isExpanded}
									<div class="result-details">
										<div class="detail-row">
											<span class="detail-label">Run ID:</span>
											<span class="detail-value">{run.RunId}</span>
										</div>
										<div class="detail-row">
											<span class="detail-label">Success:</span>
											<span class="detail-value">{run.Success ? 'Yes' : 'No'}</span>
										</div>
										<div class="detail-row">
											<span class="detail-label">Total Expectations:</span>
											<span class="detail-value">{run.TotalExpectations}</span>
										</div>
										<div class="detail-row">
											<span class="detail-label">Successful:</span>
											<span class="detail-value success">{run.SuccessfulExpectations}</span>
										</div>
										<div class="detail-row">
											<span class="detail-label">Failed:</span>
											<span class="detail-value failed">{run.FailedExpectations}</span>
										</div>
										{#if run.expectation_results && run.expectation_results.length > 0}
											<div class="expectations-section">
												<h4>Expectation Results</h4>
												{#each run.expectation_results as exp}
													<div class="expectation-item {exp.Success ? '' : 'failed'}">
														<div class="exp-header">
															<span class="exp-column">{exp.ColumnName}</span>
															<span class="exp-type">{exp.ExpectationType}</span>
															{#if exp.Success}
																<span class="exp-status success">✓</span>
															{:else}
																<span class="exp-status failed">✗</span>
															{/if}
														</div>
														{#if !exp.Success && exp.ResultDetails}
															{@const details = parseResultDetails(exp.ResultDetails)}
															<div class="exp-details">
																{#if details}
																	<pre>{JSON.stringify(details, null, 2)}</pre>
																{:else}
																	<pre>{exp.ResultDetails}</pre>
																{/if}
															</div>
														{/if}
													</div>
												{/each}
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.panel-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 99999;
		display: flex;
		justify-content: flex-end;
		animation: fadeIn 0.2s ease-out;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		will-change: auto;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.panel-container {
		width: 600px;
		max-width: 90vw;
		height: 100vh;
		background-color: #1f2937;
		border-left: 1px solid #374151;
		display: flex;
		flex-direction: column;
		box-shadow: -4px 0 20px rgba(0, 0, 0, 0.5);
		animation: slideIn 0.3s ease-out;
		overflow: hidden;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		will-change: auto;
		position: relative;
		z-index: 1;
	}

	@keyframes slideIn {
		from {
			transform: translateX(100%);
		}
		to {
			transform: translateX(0);
		}
	}

	.panel-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem;
		border-bottom: 1px solid #374151;
		flex-shrink: 0;
	}

	.panel-title {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #ffffff;
	}

	.close-button {
		background: transparent;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 1.75rem;
		height: 1.75rem;
		transition: all 0.2s;
	}

	.close-button:hover {
		background-color: #374151;
		color: #ffffff;
		border-color: var(--color-primary-light);
	}

	.close-button svg {
		width: 1rem;
		height: 1rem;
	}

	.panel-body {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}

	/* Custom scrollbar */
	.panel-body::-webkit-scrollbar {
		width: 10px;
	}

	.panel-body::-webkit-scrollbar-track {
		background: #111827;
	}

	.panel-body::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
	}

	.panel-body::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	.panel-body {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.loading-state,
	.error-state,
	.no-data-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		text-align: center;
		min-height: 200px;
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #374151;
		border-top-color: var(--color-primary-light);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 1rem;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.summary-stats {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}

	.stat-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 600;
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #d1d5db;
	}

	.stat-badge.success {
		background-color: #065f46;
		color: #d1fae5;
		border-color: #047857;
	}

	.stat-badge.failed {
		background-color: #991b1b;
		color: #fecaca;
		border-color: #b91c1c;
	}

	.filters {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 1rem;
		align-items: center;
	}

	.filter-checkbox {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #9ca3af;
		cursor: pointer;
	}

	.search-input {
		flex: 1;
		padding: 0.5rem;
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		color: #ffffff;
		font-size: 0.875rem;
	}

	.search-input:focus {
		outline: none;
		border-color: var(--color-primary-light);
		box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.1);
	}

	.results-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.result-item {
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		overflow: hidden;
	}

	.result-item.has-failures {
		border-color: #991b1b;
	}

	.result-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.result-header:hover {
		background-color: #1f2937;
	}

	.result-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		flex: 1;
	}

	.result-exchange {
		font-weight: 600;
		color: #ffffff;
		font-size: 0.875rem;
	}

	.result-product {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	.result-date {
		font-size: 0.75rem;
		color: #6b7280;
	}

	.result-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.status-badge.success {
		background-color: #065f46;
		color: #d1fae5;
	}

	.status-badge.failed {
		background-color: #991b1b;
		color: #fecaca;
	}

	.expand-icon {
		width: 1rem;
		height: 1rem;
		color: #9ca3af;
		transition: transform 0.2s;
	}

	.expand-icon.expanded {
		transform: rotate(180deg);
	}

	.result-details {
		padding: 0.75rem;
		border-top: 1px solid #374151;
		background-color: #0f172a;
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #1e293b;
		font-size: 0.875rem;
	}

	.detail-row:last-child {
		border-bottom: none;
	}

	.detail-label {
		color: #9ca3af;
	}

	.detail-value {
		color: #ffffff;
		font-weight: 500;
	}

	.detail-value.success {
		color: #10b981;
	}

	.detail-value.failed {
		color: #ef4444;
	}

	.expectations-section {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #374151;
	}

	.expectations-section h4 {
		margin: 0 0 0.75rem 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #ffffff;
	}

	.expectation-item {
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		padding: 0.75rem;
		margin-bottom: 0.5rem;
	}

	.expectation-item.failed {
		border-color: #991b1b;
	}

	.exp-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
	}

	.exp-column {
		font-weight: 600;
		color: #ffffff;
		font-size: 0.875rem;
	}

	.exp-type {
		font-size: 0.75rem;
		color: #9ca3af;
		flex: 1;
	}

	.exp-status {
		font-size: 1rem;
		font-weight: bold;
	}

	.exp-status.success {
		color: #10b981;
	}

	.exp-status.failed {
		color: #ef4444;
	}

	.exp-details {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background-color: #111827;
		border-radius: 0.25rem;
	}

	.exp-details pre {
		margin: 0;
		font-size: 0.75rem;
		color: #d1d5db;
		white-space: pre-wrap;
		word-break: break-all;
	}
</style>

