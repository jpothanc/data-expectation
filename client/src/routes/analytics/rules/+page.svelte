<script lang="ts">
	import { withTimeout } from '$lib/utils/promise';
	import {
		getRuleFailures,
		getRuleFailuresByRegion,
		getCombinedRuleStats,
		type RuleFailureData,
		type RuleFailureByRegionData,
		type CombinedRuleData
	} from '$lib/services/api';
	import BarChart from '$lib/components/BarChart.svelte';
	import GroupedBarChart from '$lib/components/GroupedBarChart.svelte';
	import ChartCard from '$lib/components/ChartCard.svelte';
	import PageControls from '$lib/components/PageControls.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import ErrorBanner from '$lib/components/ErrorBanner.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let days = $state(7);
	let combinedRuleName = $state('is_tradable_stocks');
	let isFetching = $state(false);

	let ruleFailuresData = $state<RuleFailureData[]>([]);
	let ruleFailuresByRegionData = $state<RuleFailureByRegionData[]>([]);
	let combinedRuleData = $state<CombinedRuleData | null>(null);

	async function fetchData() {
		if (isFetching) return;

		isFetching = true;
		loading = true;
		error = null;

		try {
			const results = await Promise.allSettled([
				withTimeout(getRuleFailures(days, 20), 15000),
				withTimeout(getRuleFailuresByRegion(days, 20), 15000),
				withTimeout(getCombinedRuleStats(combinedRuleName, days), 15000).catch(() => null)
			]);

			if (results[0].status === 'fulfilled') {
				ruleFailuresData = results[0].value.data;
			} else {
				console.error('Error fetching ruleFailures:', results[0].reason);
			}

			if (results[1].status === 'fulfilled') {
				ruleFailuresByRegionData = results[1].value.data;
			} else {
				console.error('Error fetching ruleFailuresByRegion:', results[1].reason);
			}

			if (results[2].status === 'fulfilled' && results[2].value) {
				combinedRuleData = results[2].value.TotalCount !== undefined ? results[2].value : null;
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
	<PageControls {days} onDaysChange={(d) => { days = d; fetchData(); }} onRefresh={fetchData} {loading}>
		{#snippet additionalControls()}
			<div class="control-group">
				<label for="rule">Rule:</label>
				<select id="rule" bind:value={combinedRuleName} onchange={fetchData}>
					<option value="is_tradable_stocks">is_tradable_stocks</option>
				</select>
			</div>
		{/snippet}
	</PageControls>

	{#if error}
		<ErrorBanner message={error} />
	{/if}

	{#if loading}
		<LoadingState message="Loading rule analysis data..." />
	{:else}
		<div class="charts-grid">
			<ChartCard title="Rule Failure Statistics" stats={[
				{ label: 'Rules', value: ruleFailuresData.length }
			]}>
				{#if ruleFailuresData.length > 0}
					<BarChart data={ruleFailuresData} height="400px" />
				{:else}
					<EmptyState message="No rule failures found" />
				{/if}
			</ChartCard>

			<ChartCard title="Rule Failures by Region" stats={[
				{ label: 'Regions', value: [...new Set(ruleFailuresByRegionData.map(d => d.Region))].length },
				{ label: 'Rules', value: [...new Set(ruleFailuresByRegionData.map(d => d.RuleName))].length }
			]}>
				{#if ruleFailuresByRegionData.length > 0}
					<GroupedBarChart data={ruleFailuresByRegionData} height="400px" />
				{:else}
					<EmptyState message="No rule failures by region found" />
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
								<span class="stat-percent">({((combinedRuleData.TradableCount / combinedRuleData.TotalCount) * 100).toFixed(1)}%)</span>
							</div>
							<div class="stat-row">
								<span class="stat-label">Not Tradable:</span>
								<span class="stat-value failed">{combinedRuleData.NotTradableCount}</span>
								<span class="stat-percent">({((combinedRuleData.NotTradableCount / combinedRuleData.TotalCount) * 100).toFixed(1)}%)</span>
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
					<EmptyState message="No data available for {combinedRuleName}" />
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

	.charts-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.charts-grid > :nth-child(3) {
		grid-column: 1 / -1;
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

	.stat-value.success { color: #10b981; }
	.stat-value.failed { color: #ef4444; }

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

	.reason-column { font-weight: 600; color: #e5e7eb; }
	.reason-type { color: #9ca3af; font-style: italic; }
	.reason-count { color: #f87171; font-weight: 600; }

	@media (max-width: 768px) {
		.page-container { padding: 1rem; }
		.charts-grid { grid-template-columns: 1fr; }
	}
</style>
