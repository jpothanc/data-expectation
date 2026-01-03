<script lang="ts">
	import { goto } from '$app/navigation';
	import {
		getRuleFailures,
		getCombinedRuleStats,
		type RuleFailureData,
		type CombinedRuleData
	} from '$lib/services/api';
	import BarChart from '$lib/components/BarChart.svelte';
	import ChartCard from '$lib/components/ChartCard.svelte';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let days = $state(7);
	let combinedRuleName = $state('is_tradable_stocks');
	let isFetching = $state(false);

	let ruleFailuresData = $state<RuleFailureData[]>([]);
	let combinedRuleData = $state<CombinedRuleData | null>(null);

	async function fetchData() {
		if (isFetching) return;
		
		isFetching = true;
		loading = true;
		error = null;

		try {
			const withTimeout = <T>(promise: Promise<T>, timeoutMs: number): Promise<T> => {
				return Promise.race([
					promise,
					new Promise<T>((_, reject) => 
						setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
					)
				]);
			};
			
			const results = await Promise.allSettled([
				withTimeout(getRuleFailures(days, 20), 15000),
				withTimeout(getCombinedRuleStats(combinedRuleName, days), 15000).catch(() => null)
			]);

			if (results[0].status === 'fulfilled') {
				ruleFailuresData = results[0].value.data;
			} else {
				console.error('Error fetching ruleFailures:', results[0].reason);
			}

			if (results[1].status === 'fulfilled' && results[1].value) {
				if (results[1].value.TotalCount !== undefined) {
					combinedRuleData = results[1].value;
				} else {
					combinedRuleData = null;
				}
			} else {
				combinedRuleData = null;
			}
		} catch (err) {
			console.error('Error fetching rules data:', err);
			error = err instanceof Error ? err.message : 'An unknown error occurred';
		} finally {
			loading = false;
			isFetching = false;
		}
	}


	let initialFetchDone = $state(false);
	
	$effect(() => {
		if (!initialFetchDone) {
			initialFetchDone = true;
			setTimeout(() => {
				fetchData().catch(err => {
					console.error('Error in initial fetch:', err);
					loading = false;
					isFetching = false;
					error = err instanceof Error ? err.message : 'Failed to load data';
				});
			}, 0);
		}
	});
</script>

<div class="page-container">
	<div class="page-controls">
		<div class="control-group">
			<label for="days">Period:</label>
			<select id="days" bind:value={days} onchange={fetchData}>
				<option value={7}>7 Days</option>
				<option value={14}>14 Days</option>
				<option value={30}>30 Days</option>
			</select>
		</div>
		<div class="control-group">
			<label for="rule">Rule:</label>
			<select id="rule" bind:value={combinedRuleName} onchange={fetchData}>
				<option value="is_tradable_stocks">is_tradable_stocks</option>
			</select>
		</div>
		<button class="refresh-button" onclick={fetchData} disabled={loading} type="button" title="Refresh data">
			{#if loading}
				<svg class="refresh-icon spinning" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			{:else}
				<svg class="refresh-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			{/if}
		</button>
	</div>

	{#if error}
		<div class="error">
			<p>Error: {error}</p>
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading rule analysis data...</p>
		</div>
	{:else}
		<div class="charts-grid">
			<ChartCard title="Rule Failure Statistics" stats={[
				{ label: 'Rules', value: ruleFailuresData.length }
			]}>
				{#if ruleFailuresData.length > 0}
					<BarChart data={ruleFailuresData} height="400px" />
				{:else}
					<div class="no-data-message">
						<p>No rule failures found</p>
					</div>
				{/if}
			</ChartCard>

			<ChartCard title="Combined Rule: {combinedRuleName}" stats={combinedRuleData ? [
				{ label: 'Tradable', value: combinedRuleData.TradableCount, highlight: 'success' },
				{ label: 'Not Tradable', value: combinedRuleData.NotTradableCount, highlight: 'failed' },
				{ label: 'Total', value: combinedRuleData.TotalCount }
			] : []}>
				{#if combinedRuleData && combinedRuleData.TotalCount > 0}
					<div class="combined-rule-content">
						<div class="combined-rule-stats">
							<div class="stat-row">
								<span class="stat-label">Tradable:</span>
								<span class="stat-value success">{combinedRuleData.TradableCount}</span>
								<span class="stat-percent">
									({((combinedRuleData.TradableCount / combinedRuleData.TotalCount) * 100).toFixed(1)}%)
								</span>
							</div>
							<div class="stat-row">
								<span class="stat-label">Not Tradable:</span>
								<span class="stat-value failed">{combinedRuleData.NotTradableCount}</span>
								<span class="stat-percent">
									({((combinedRuleData.NotTradableCount / combinedRuleData.TotalCount) * 100).toFixed(1)}%)
								</span>
							</div>
						</div>
						{#if combinedRuleData.FailureReasons.length > 0}
							<div class="failure-reasons">
								<h4>Failure Reasons:</h4>
								<ul>
									{#each combinedRuleData.FailureReasons as reason}
										<li>
											<span class="reason-column">{reason.ColumnName}</span>
											<span class="reason-type">{reason.ExpectationType}</span>
											<span class="reason-count">({reason.FailureCount})</span>
										</li>
									{/each}
								</ul>
							</div>
						{/if}
					</div>
				{:else}
					<div class="no-data-message">
						<p>No data available for {combinedRuleName}</p>
					</div>
				{/if}
			</ChartCard>
		</div>
	{/if}
</div>

<style>
	.page-container {
		max-width: 1600px;
		margin: 0 auto;
		padding: 1.25rem 2rem;
		min-height: calc(100vh - 60px);
	}

	.page-controls {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 0.75rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}

	.control-group {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.control-group label {
		font-size: 0.75rem;
		color: #9ca3af;
		font-weight: 500;
		white-space: nowrap;
	}

	.control-group select {
		padding: 0.375rem 0.625rem;
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #e5e7eb;
		font-size: 0.75rem;
		cursor: pointer;
		transition: border-color 0.2s;
	}

	.refresh-button {
		background-color: #1f2937;
		border: 1px solid #374151;
		color: #9ca3af;
		padding: 0;
		border-radius: 0.375rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		width: 2rem;
		height: 2rem;
	}

	.refresh-button:hover:not(:disabled) {
		background-color: #059669;
		border-color: #059669;
		color: white;
	}

	.refresh-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		background: #374151;
	}

	.refresh-icon {
		width: 1rem;
		height: 1rem;
	}

	.refresh-icon.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error {
		margin-top: 1.5rem;
		padding: 1rem;
		background-color: #7f1d1d;
		border: 1px solid #dc2626;
		border-radius: 0.5rem;
		color: #fca5a5;
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 4rem 2rem;
		gap: 1rem;
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #374151;
		border-top-color: #34d399;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.charts-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.no-data-message {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 150px;
		color: #6b7280;
		font-size: 0.875rem;
		background: rgba(55, 65, 81, 0.3);
		border-radius: 0.5rem;
		border: 1px dashed #374151;
	}

	.combined-rule-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.combined-rule-stats {
		padding: 1rem;
		background-color: #1f2937;
		border-radius: 0.5rem;
		border: 1px solid #374151;
	}

	.stat-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 0;
		border-bottom: 1px solid rgba(55, 65, 81, 0.5);
	}

	.stat-row:last-child {
		border-bottom: none;
	}

	.stat-label {
		font-size: 0.875rem;
		color: #9ca3af;
		font-weight: 500;
	}

	.stat-value {
		font-size: 1.125rem;
		font-weight: 600;
		color: #e5e7eb;
	}

	.stat-value.success {
		color: #10b981;
	}

	.stat-value.failed {
		color: #ef4444;
	}

	.stat-percent {
		font-size: 0.8125rem;
		color: #6b7280;
		margin-left: 0.5rem;
	}

	.failure-reasons {
		margin-top: 1rem;
		padding: 1rem;
		background-color: #1f2937;
		border-radius: 0.5rem;
		border: 1px solid #374151;
	}

	.failure-reasons h4 {
		margin: 0 0 0.75rem 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #34d399;
	}

	.failure-reasons ul {
		margin: 0;
		padding-left: 1.25rem;
		list-style: none;
	}

	.failure-reasons li {
		margin-bottom: 0.5rem;
		font-size: 0.8125rem;
		color: #d1d5db;
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.reason-column {
		font-weight: 600;
		color: #e5e7eb;
	}

	.reason-type {
		color: #9ca3af;
		font-style: italic;
	}

	.reason-count {
		color: #f87171;
		font-weight: 600;
	}

	@media (max-width: 768px) {
		.page-container {
			padding: 1rem;
		}

		.charts-grid {
			grid-template-columns: 1fr;
		}
	}
</style>


