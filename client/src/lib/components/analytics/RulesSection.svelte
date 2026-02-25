<script lang="ts">
	import BarChart from '../charts/BarChart.svelte';
	import ChartCard from '../charts/ChartCard.svelte';
	import type { RuleFailureData, CombinedRuleData } from '$lib/services/api';

	interface Props {
		ruleFailuresData: RuleFailureData[];
		combinedRuleData: CombinedRuleData | null;
		combinedRuleName: string;
	}

	let { ruleFailuresData, combinedRuleData, combinedRuleName }: Props = $props();
</script>

<div class="section-grid">
	<ChartCard title="Rule Failure Statistics" stats={[
		{ label: 'Rules', value: ruleFailuresData.length }
	]}>
		{#if ruleFailuresData.length > 0}
			<BarChart data={ruleFailuresData} height="280px" />
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

<style>
	.section-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}

	.no-data-message {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100px;
		color: #6b7280;
		font-size: 0.6875rem;
		background: rgba(55, 65, 81, 0.3);
		border-radius: 0.25rem;
		border: 1px dashed #374151;
	}

	.combined-rule-content {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.combined-rule-stats {
		padding: 0.625rem;
		background-color: #1f2937;
		border-radius: 0.25rem;
		border: 1px solid #374151;
	}

	.stat-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.375rem 0;
		border-bottom: 1px solid rgba(55, 65, 81, 0.5);
	}

	.stat-row:last-child {
		border-bottom: none;
	}

	.stat-label {
		font-size: 0.6875rem;
		color: #9ca3af;
		font-weight: 500;
	}

	.stat-value {
		font-size: 0.875rem;
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
		font-size: 0.6875rem;
		color: #6b7280;
		margin-left: 0.25rem;
	}

	.failure-reasons {
		margin-top: 0.5rem;
		padding: 0.625rem;
		background-color: #1f2937;
		border-radius: 0.25rem;
		border: 1px solid #374151;
	}

	.failure-reasons h4 {
		margin: 0 0 0.375rem 0;
		font-size: 0.6875rem;
		font-weight: 600;
		color: #34d399;
	}

	.failure-reasons ul {
		margin: 0;
		padding-left: 0.875rem;
		list-style: none;
	}

	.failure-reasons li {
		margin-bottom: 0.25rem;
		font-size: 0.6875rem;
		color: #d1d5db;
		display: flex;
		gap: 0.25rem;
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
		.section-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

