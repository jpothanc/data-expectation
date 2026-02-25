<script lang="ts">
	import { withTimeout } from '$lib/utils/promise';
	import {
		getGlobalView,
		getHeatmap,
		getExpectationFailuresByRegion,
		type GlobalViewData,
		type HeatmapData,
		type ExpectationFailureByRegionData
	} from '$lib/services/api';
	import OverviewSection from '$lib/components/analytics/OverviewSection.svelte';
	import PageControls from '$lib/components/ui/PageControls.svelte';
	import LoadingState from '$lib/components/ui/LoadingState.svelte';
	import ErrorBanner from '$lib/components/ui/ErrorBanner.svelte';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let days = $state(7);
	let isFetching = $state(false);

	let globalViewData = $state<GlobalViewData[]>([]);
	let heatmapData = $state<HeatmapData[]>([]);
	let expectationFailuresByRegionData = $state<ExpectationFailureByRegionData[]>([]);

	async function fetchAllData() {
		if (isFetching) return;

		isFetching = true;
		loading = true;
		error = null;

		try {
			const results = await Promise.allSettled([
				withTimeout(getGlobalView(days), 15000),
				withTimeout(getHeatmap(days), 15000),
				withTimeout(getExpectationFailuresByRegion(days, 20), 15000)
			]);

			if (results[0].status === 'fulfilled') {
				globalViewData = results[0].value.data;
			} else {
				console.error('Error fetching globalView:', results[0].reason);
				error = `Failed to load global view: ${results[0].reason instanceof Error ? results[0].reason.message : String(results[0].reason)}`;
			}

			if (results[1].status === 'fulfilled') {
				heatmapData = results[1].value.data;
			} else {
				console.error('Error fetching heatmap:', results[1].reason);
				if (!error) error = `Failed to load heatmap: ${results[1].reason instanceof Error ? results[1].reason.message : String(results[1].reason)}`;
			}

			if (results[2].status === 'fulfilled') {
				expectationFailuresByRegionData = results[2].value.data;
			} else {
				console.error('Error fetching expectationFailuresByRegion:', results[2].reason);
				if (!error) error = `Failed to load expectation failures: ${results[2].reason instanceof Error ? results[2].reason.message : String(results[2].reason)}`;
			}

			if (results.every(r => r.status === 'rejected')) {
				error = 'Failed to load analytics data. Please ensure the server is running at http://127.0.0.1:5006';
			}
		} catch (err) {
			console.error('Unexpected error fetching data:', err);
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
				fetchAllData().catch(err => {
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
	<PageControls {days} onDaysChange={(d) => { days = d; fetchAllData(); }} onRefresh={fetchAllData} {loading} />

	{#if error}
		<ErrorBanner message={error} />
	{/if}

	{#if loading}
		<LoadingState message="Loading analytics data..." />
	{:else}
		<OverviewSection
			{globalViewData}
			{heatmapData}
			{expectationFailuresByRegionData}
			{days}
		/>
	{/if}
</div>

<style>
	.page-container {
		max-width: 1600px;
		margin: 0 auto;
		padding: 1.25rem 2rem;
		min-height: calc(100vh - 60px);
	}

	@media (max-width: 768px) {
		.page-container {
			padding: 1rem;
		}
	}
</style>
