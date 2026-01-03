<script lang="ts">
	import RefreshButton from './RefreshButton.svelte';
	import { PERIOD_OPTIONS, type PeriodOption } from '../constants/periods';

	interface Props {
		days: number;
		onDaysChange: (days: number) => void;
		onRefresh: () => void;
		loading?: boolean;
		additionalControls?: any;
	}

	let {
		days,
		onDaysChange,
		onRefresh,
		loading = false,
		additionalControls
	}: Props = $props();

	function handleDaysChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		onDaysChange(Number(target.value));
	}
</script>

<div class="page-controls">
	<div class="control-group">
		<label for="days">Period:</label>
		<select id="days" value={days} onchange={handleDaysChange}>
			{#each PERIOD_OPTIONS as option}
				<option value={option.value}>{option.label}</option>
			{/each}
		</select>
	</div>
	{@render additionalControls?.()}
	<RefreshButton {loading} onClick={onRefresh} />
</div>

<style>
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

	.control-group select:hover {
		border-color: #4b5563;
	}

	.control-group select:focus {
		outline: none;
		border-color: var(--color-primary-light);
	}
</style>

