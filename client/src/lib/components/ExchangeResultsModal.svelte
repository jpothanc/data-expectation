<script lang="ts">
	import type { ExchangeValidationResult } from '../services/api';

	interface Props {
		exchange: string;
		results: ExchangeValidationResult[];
		onClose: () => void;
	}

	let { exchange, results, onClose }: Props = $props();

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

	function safeToFixed(value: number | string | null | undefined, decimals: number = 1): string {
		if (value === null || value === undefined) return '0';
		const num = typeof value === 'string' ? parseFloat(value) : value;
		if (isNaN(num)) return '0';
		return num.toFixed(decimals);
	}

	function toggleRun(runId: number) {
		if (expandedRuns.has(runId)) {
			expandedRuns.delete(runId);
		} else {
			expandedRuns.add(runId);
		}
		expandedRuns = new Set(expandedRuns);
	}

	function isRunExpanded(runId: number): boolean {
		return expandedRuns.has(runId);
	}

	// Filter results based on search and filter
	const filteredResults = $derived.by(() => {
		return results.filter(run => {
			// Filter by status
			if (showOnlyFailed && run.Success) return false;
			
			// Filter by search term
			if (searchTerm) {
				const term = searchTerm.toLowerCase();
				return (
					run.RunId.toString().includes(term) ||
					run.Region.toLowerCase().includes(term) ||
					run.ProductType.toLowerCase().includes(term) ||
					run.rules_applied.some(r => r.RuleName.toLowerCase().includes(term)) ||
					run.expectation_results.some(e => e.ColumnName.toLowerCase().includes(term))
				);
			}
			return true;
		});
	});

	// Calculate summary stats
	const summary = $derived.by(() => {
		const total = results.length;
		const successful = results.filter(r => r.Success).length;
		const failed = total - successful;
		const totalExpectations = results.reduce((sum, r) => sum + r.TotalExpectations, 0);
		const passedExpectations = results.reduce((sum, r) => sum + r.SuccessfulExpectations, 0);
		const failedExpectations = results.reduce((sum, r) => sum + r.FailedExpectations, 0);
		
		return {
			total,
			successful,
			failed,
			successRate: total > 0 ? ((successful / total) * 100).toFixed(1) : '0',
			totalExpectations,
			passedExpectations,
			failedExpectations,
			expectationSuccessRate: totalExpectations > 0 ? ((passedExpectations / totalExpectations) * 100).toFixed(1) : '0'
		};
	});

	// Auto-expand failed runs
	$effect(() => {
		if (showOnlyFailed) {
			const failedRunIds = results.filter(r => !r.Success).map(r => r.RunId);
			expandedRuns = new Set(failedRunIds);
		}
	});
</script>

<div class="modal-overlay" onclick={onClose} role="dialog" aria-modal="true" aria-labelledby="modal-title">
	<div class="modal-content" onclick={(e) => e.stopPropagation()} role="document">
		<div class="modal-header">
			<div class="header-content">
				<h2 id="modal-title">Validation Results: {exchange}</h2>
				<div class="header-stats">
					<span class="stat-badge success">{summary.successful} Passed</span>
					<span class="stat-badge failed">{summary.failed} Failed</span>
					<span class="stat-badge">{summary.total} Total</span>
				</div>
			</div>
			<button class="close-button" onclick={(e) => { e.preventDefault(); e.stopPropagation(); onClose(); }} type="button" aria-label="Close" title="Close">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="modal-body">
			{#if results.length === 0}
				<div class="no-data">
					<p>No validation results found for {exchange}</p>
				</div>
			{:else}
				<!-- Summary Cards -->
				<div class="summary-cards">
					<div class="summary-card">
						<div class="summary-card-label">Success Rate</div>
						<div class="summary-card-value success">{summary.successRate}%</div>
						<div class="summary-card-detail">{summary.successful} of {summary.total} runs</div>
					</div>
					<div class="summary-card">
						<div class="summary-card-label">Expectations</div>
						<div class="summary-card-value">{summary.expectationSuccessRate}%</div>
						<div class="summary-card-detail">{summary.passedExpectations} of {summary.totalExpectations} passed</div>
					</div>
					<div class="summary-card">
						<div class="summary-card-label">Failed Expectations</div>
						<div class="summary-card-value failed">{summary.failedExpectations}</div>
						<div class="summary-card-detail">Across all runs</div>
					</div>
				</div>

				<!-- Filters -->
				<div class="filters">
					<div class="filter-group">
						<label class="filter-checkbox">
							<input type="checkbox" bind:checked={showOnlyFailed} />
							<span>Show only failed runs</span>
						</label>
					</div>
					<div class="filter-group">
						<input 
							type="text" 
							class="search-input" 
							placeholder="Search by run ID, region, column, rule..." 
							bind:value={searchTerm}
						/>
					</div>
				</div>

				<!-- Runs List -->
				<div class="runs-list">
					{#each filteredResults as run}
						{@const isExpanded = isRunExpanded(run.RunId)}
						{@const failedExpectations = run.expectation_results.filter(e => !e.Success)}
						<div class="run-card {run.Success ? 'success' : 'failed'}">
							<div class="run-header" onclick={() => toggleRun(run.RunId)}>
								<div class="run-info">
									<div class="run-title-row">
										<h3>Run #{run.RunId}</h3>
										<span class="status-badge {run.Success ? 'success' : 'failed'}">
											{run.Success ? '✅ Passed' : '❌ Failed'}
										</span>
									</div>
									<p class="run-meta">
										<span>{formatDate(run.RunTimestamp)}</span>
										<span class="separator">•</span>
										<span>{run.Region} / {run.ProductType}</span>
									</p>
								</div>
								<div class="run-stats-compact">
									<div class="stat-compact">
										<span class="stat-value {run.Success ? 'success' : 'failed'}">{run.SuccessfulExpectations}/{run.TotalExpectations}</span>
										<span class="stat-label">Passed</span>
									</div>
									{#if failedExpectations.length > 0}
										<div class="stat-compact">
											<span class="stat-value failed">{failedExpectations.length}</span>
											<span class="stat-label">Failed</span>
										</div>
									{/if}
									<div class="expand-icon {isExpanded ? 'expanded' : ''}">
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
										</svg>
									</div>
								</div>
							</div>

							{#if isExpanded}
								<div class="run-details">
									<!-- Rules Applied -->
									{#if run.rules_applied.length > 0}
										<div class="detail-section">
											<h4>Rules Applied ({run.rules_applied.length})</h4>
											<div class="rules-list">
												{#each run.rules_applied as rule}
													<span class="rule-tag {rule.RuleType?.toLowerCase() || ''}">
														{rule.RuleName}
														{#if rule.RuleType}
															<span class="rule-type">{rule.RuleType}</span>
														{/if}
													</span>
												{/each}
											</div>
										</div>
									{/if}

									<!-- Expectations - Show failed first, then all -->
									{#if run.expectation_results.length > 0}
										<div class="detail-section">
											<h4>
												Expectations ({run.expectation_results.length})
												{#if failedExpectations.length > 0}
													<span class="failed-count">({failedExpectations.length} failed)</span>
												{/if}
											</h4>
											
											{#if failedExpectations.length > 0}
												<div class="expectations-group">
													<h5 class="group-title failed">Failed Expectations</h5>
													<div class="expectations-compact">
														{#each failedExpectations as exp}
															<div class="expectation-item failed">
																<div class="exp-header">
																	<span class="exp-column">{exp.ColumnName}</span>
																	<span class="exp-type">{exp.ExpectationType}</span>
																</div>
																<div class="exp-details">
																	{#if exp.UnexpectedCount && exp.UnexpectedCount > 0}
																		<span class="exp-stat">Unexpected: {exp.UnexpectedCount} ({safeToFixed(exp.UnexpectedPercent)}%)</span>
																	{/if}
																	{#if exp.MissingCount && exp.MissingCount > 0}
																		<span class="exp-stat">Missing: {exp.MissingCount} ({safeToFixed(exp.MissingPercent)}%)</span>
																	{/if}
																</div>
																{#if exp.ResultDetails}
																	{@const details = parseResultDetails(exp.ResultDetails)}
																	{#if details && details.partial_unexpected_counts && details.partial_unexpected_counts.length > 0}
																		<div class="unexpected-values">
																			<strong>Values:</strong>
																			<div class="value-list">
																				{#each details.partial_unexpected_counts.slice(0, 5) as item}
																					<code>{String(item.value)}</code> <span>({item.count}x)</span>
																				{/each}
																				{#if details.partial_unexpected_counts.length > 5}
																					<span class="more-values">+{details.partial_unexpected_counts.length - 5} more</span>
																				{/if}
																			</div>
																		</div>
																	{/if}
																{/if}
															</div>
														{/each}
													</div>
												</div>
											{/if}

											{#if run.expectation_results.length > failedExpectations.length}
												<div class="expectations-group">
													<h5 class="group-title success">Passed Expectations ({run.expectation_results.length - failedExpectations.length})</h5>
													<div class="expectations-compact passed">
														{#each run.expectation_results.filter(e => e.Success) as exp}
															<div class="expectation-item success">
																<span class="exp-column">{exp.ColumnName}</span>
																<span class="exp-type">{exp.ExpectationType}</span>
															</div>
														{/each}
													</div>
												</div>
											{/if}
										</div>
									{/if}
								</div>
							{/if}
						</div>
					{/each}
				</div>

				{#if filteredResults.length === 0}
					<div class="no-results">
						<p>No runs match your filters</p>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed !important;
		top: 0 !important;
		left: 0 !important;
		right: 0 !important;
		bottom: 0 !important;
		width: 100vw !important;
		height: 100vh !important;
		background-color: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 99999 !important;
		padding: 1rem;
		overflow-y: auto;
		pointer-events: auto;
		margin: 0 !important;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		transform: translateZ(0);
		-webkit-transform: translateZ(0);
		will-change: auto;
	}

	.modal-content {
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		max-width: 800px;
		width: 90vw;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		flex-shrink: 0;
		position: fixed !important;
		top: 50% !important;
		left: 50% !important;
		transform: translate(-50%, -50%) translateZ(0) !important;
		-webkit-transform: translate(-50%, -50%) translateZ(0) !important;
		margin: 0 !important;
		will-change: auto;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #374151;
		gap: 0.75rem;
	}

	.header-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.modal-header h2 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #ffffff;
		line-height: 1.4;
	}

	.header-stats {
		display: flex;
		gap: 0.375rem;
		flex-wrap: wrap;
	}

	.stat-badge {
		padding: 0.1875rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.6875rem;
		font-weight: 600;
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #d1d5db;
		line-height: 1.2;
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
		transition: all 0.2s;
		flex-shrink: 0;
		width: 1.75rem;
		height: 1.75rem;
		z-index: 10;
		position: relative;
		min-width: 1.75rem;
		min-height: 1.75rem;
	}

	.close-button:hover {
		background-color: #374151;
		color: #ffffff;
		border-color: #34d399;
	}

	.close-button svg {
		width: 1rem;
		height: 1rem;
	}

	.modal-body {
		padding: 1rem 1.25rem;
		overflow-y: auto;
		flex: 1;
	}

	/* Custom scrollbar styling with theme */
	.modal-body::-webkit-scrollbar,
	.modal-content::-webkit-scrollbar {
		width: 10px;
	}

	.modal-body::-webkit-scrollbar-track,
	.modal-content::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 5px;
	}

	.modal-body::-webkit-scrollbar-thumb,
	.modal-content::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 5px;
		border: 2px solid #111827;
	}

	.modal-body::-webkit-scrollbar-thumb:hover,
	.modal-content::-webkit-scrollbar-thumb:hover {
		background: var(--color-primary);
	}

	/* Firefox scrollbar */
	.modal-body,
	.modal-content {
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	.no-data, .no-results {
		text-align: center;
		padding: 3rem;
		color: #9ca3af;
	}

	/* Summary Cards */
	.summary-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.summary-card {
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.summary-card-label {
		font-size: 0.6875rem;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.summary-card-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #ffffff;
	}

	.summary-card-value.success {
		color: #10b981;
	}

	.summary-card-value.failed {
		color: #ef4444;
	}

	.summary-card-detail {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	/* Filters */
	.filters {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 1rem;
		padding: 0.75rem;
		background-color: #111827;
		border-radius: 0.375rem;
		border: 1px solid #374151;
		flex-wrap: wrap;
		align-items: center;
	}

	.filter-group {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.filter-checkbox {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		cursor: pointer;
		color: #d1d5db;
		font-size: 0.8125rem;
	}

	.filter-checkbox input[type="checkbox"] {
		cursor: pointer;
	}

	.search-input {
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		padding: 0.4375rem 0.625rem;
		color: #e5e7eb;
		font-size: 0.8125rem;
		min-width: 200px;
	}

	.search-input:focus {
		outline: none;
		border-color: #34d399;
	}

	/* Runs List */
	.runs-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.run-card {
		background-color: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		overflow: hidden;
		transition: all 0.2s;
	}

	.run-card.success {
		border-left: 4px solid #10b981;
	}

	.run-card.failed {
		border-left: 4px solid #ef4444;
	}

	.run-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		cursor: pointer;
		transition: background-color 0.2s;
		gap: 0.75rem;
	}

	.run-header:hover {
		background-color: #1f2937;
	}

	.run-info {
		flex: 1;
		min-width: 0;
	}

	.run-title-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.375rem;
		flex-wrap: wrap;
	}

	.run-info h3 {
		margin: 0;
		font-size: 0.9375rem;
		color: #ffffff;
		font-weight: 600;
	}

	.run-meta {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		margin: 0;
		font-size: 0.75rem;
		color: #9ca3af;
		flex-wrap: wrap;
	}

	.separator {
		color: #374151;
	}

	.status-badge {
		padding: 0.1875rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.6875rem;
		font-weight: 600;
		white-space: nowrap;
	}

	.status-badge.success {
		background-color: #065f46;
		color: #d1fae5;
	}

	.status-badge.failed {
		background-color: #991b1b;
		color: #fecaca;
	}

	.run-stats-compact {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.stat-compact {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.125rem;
	}

	.stat-compact .stat-value {
		font-size: 0.875rem;
		font-weight: 700;
		color: #ffffff;
	}

	.stat-compact .stat-value.success {
		color: #10b981;
	}

	.stat-compact .stat-value.failed {
		color: #ef4444;
	}

	.stat-compact .stat-label {
		font-size: 0.6875rem;
		color: #9ca3af;
	}

	.expand-icon {
		width: 1.25rem;
		height: 1.25rem;
		color: #9ca3af;
		transition: transform 0.2s;
		flex-shrink: 0;
	}

	.expand-icon.expanded {
		transform: rotate(180deg);
	}

	.expand-icon svg {
		width: 100%;
		height: 100%;
	}

	/* Run Details */
	.run-details {
		padding: 0 1rem 1rem 1rem;
		border-top: 1px solid #374151;
		background-color: #0f1419;
	}

	.detail-section {
		margin-top: 1rem;
	}

	.detail-section:first-child {
		margin-top: 0.75rem;
	}

	.detail-section h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.8125rem;
		font-weight: 600;
		color: #34d399;
		display: flex;
		align-items: center;
		gap: 0.375rem;
	}

	.failed-count {
		color: #ef4444;
		font-weight: 400;
	}

	.rules-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.375rem;
	}

	.rule-tag {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.6875rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #d1d5db;
	}

	.rule-type {
		font-size: 0.5625rem;
		color: #9ca3af;
		text-transform: uppercase;
	}

	/* Expectations */
	.expectations-group {
		margin-top: 0.75rem;
	}

	.group-title {
		margin: 0 0 0.5rem 0;
		font-size: 0.75rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.group-title.failed {
		color: #ef4444;
	}

	.group-title.success {
		color: #10b981;
	}

	.expectations-compact {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.expectations-compact.passed {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 0.375rem;
	}

	.expectation-item {
		padding: 0.5rem 0.625rem;
		border-radius: 0.25rem;
		border: 1px solid #374151;
		background-color: #1f2937;
	}

	.expectation-item.failed {
		border-color: #ef4444;
		background-color: rgba(239, 68, 68, 0.1);
	}

	.expectation-item.success {
		border-color: #374151;
		background-color: rgba(16, 185, 129, 0.05);
	}

	.exp-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.375rem;
		flex-wrap: wrap;
	}

	.exp-column {
		font-weight: 600;
		color: #e5e7eb;
		font-size: 0.8125rem;
	}

	.exp-type {
		font-family: monospace;
		font-size: 0.6875rem;
		color: #9ca3af;
	}

	.exp-details {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin-top: 0.375rem;
	}

	.exp-stat {
		font-size: 0.75rem;
		color: #d1d5db;
	}

	.unexpected-values {
		margin-top: 0.5rem;
		padding-top: 0.5rem;
		border-top: 1px solid #374151;
	}

	.unexpected-values strong {
		display: block;
		margin-bottom: 0.375rem;
		color: #f87171;
		font-size: 0.75rem;
	}

	.value-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.375rem;
		font-size: 0.6875rem;
	}

	.value-list code {
		background-color: #374151;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-family: monospace;
		color: #fbbf24;
	}

	.value-list span {
		color: #9ca3af;
	}

	.more-values {
		color: #34d399;
		font-style: italic;
	}

	@media (max-width: 768px) {
		.modal-overlay {
			padding: 1rem;
		}

		.modal-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.header-stats {
			width: 100%;
		}

		.summary-cards {
			grid-template-columns: 1fr;
		}

		.filters {
			flex-direction: column;
			align-items: stretch;
		}

		.search-input {
			width: 100%;
			min-width: auto;
		}

		.run-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.run-stats-compact {
			width: 100%;
			justify-content: space-between;
		}

		.expectations-compact.passed {
			grid-template-columns: 1fr;
		}
	}
</style>
