<script lang="ts">
	import { formatHeaderName } from '../utils/formatters';

	interface Props {
		headers: string[];
		data: Array<Record<string, any>>;
		title?: string;
		maxHeight?: string;
		ricColumn?: string;
		onRicClick?: (row: Record<string, any>, index: number) => void;
		onRowClick?: (row: Record<string, any>, index: number) => void;
	}

	let { headers, data, title, maxHeight = '600px', ricColumn = 'RIC', onRicClick, onRowClick }: Props = $props();
</script>

{#if data.length > 0 && headers.length > 0}
	<div class="table-wrapper">
		{#if title}
			<h2 class="table-title">{title}</h2>
		{/if}
		<div class="table-container" style="max-height: {maxHeight};">
			<table class="data-table">
				<thead>
					<tr>
						{#each headers as header}
							<th class={header === ricColumn ? 'ric-header' : ''}>{formatHeaderName(header)}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each data as row, rowIndex}
						<tr
							class={onRowClick ? 'clickable-row' : ''}
							onclick={onRowClick ? () => onRowClick(row, rowIndex) : undefined}
							onkeydown={onRowClick ? (e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									onRowClick(row, rowIndex);
								}
							} : undefined}
							role={onRowClick ? 'button' : undefined}
							tabindex={onRowClick ? 0 : undefined}
						>
							{#each headers as header}
								<td
									class="cell {header === ricColumn ? 'ric-cell' : ''} {header === ricColumn && onRicClick ? 'ric-cell-clickable' : ''}"
									onclick={header === ricColumn && onRicClick ? (e) => {
										e.stopPropagation();
										onRicClick(row, rowIndex);
									} : undefined}
								>
									{#if row[header]}
										{row[header]}
									{:else}
										<span class="empty-value">—</span>
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
{:else}
	<div class="info-message">
		<p>No data available.</p>
	</div>
{/if}

<style>
	.table-wrapper {
		margin-top: 2rem;
	}

	.table-title {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
		color: #ffffff;
		padding: 0 0.5rem;
	}

	.table-container {
		border: 1px solid #374151;
		border-radius: 0.5rem;
		overflow: auto;
		background-color: #111827;
		/* Firefox scrollbar */
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #111827;
	}

	/* Custom scrollbar styling with theme */
	.table-container::-webkit-scrollbar {
		width: 12px;
		height: 12px;
	}

	.table-container::-webkit-scrollbar-track {
		background: #111827;
		border-radius: 6px;
	}

	.table-container::-webkit-scrollbar-thumb {
		background-color: var(--color-primary-dark);
		border-radius: 6px;
		border: 2px solid #111827;
	}

	.table-container::-webkit-scrollbar-thumb:hover {
		background-color: var(--color-primary);
	}

	.table-container::-webkit-scrollbar-corner {
		background: #111827;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.data-table thead {
		position: sticky;
		top: -1px;
		background-color: #1f2937;
		z-index: 10;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
	}

	.data-table thead tr {
		position: relative;
	}

	.data-table th {
		padding: 0.5rem 0.75rem;
		text-align: left;
		font-weight: 600;
		font-size: 0.8125rem;
		color: #e5e7eb;
		border-bottom: 2px solid #4b5563;
		background-color: #1f2937;
		white-space: nowrap;
		min-width: 100px;
		border-top: 1px solid #374151;
	}

	.data-table th.ric-header {
		min-width: 120px;
		white-space: nowrap;
	}

	.data-table td {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #374151;
		color: #e5e7eb;
		word-break: break-word;
		min-width: 100px;
		max-width: 300px;
	}

	.data-table td.ric-cell {
		min-width: 120px;
		max-width: 150px;
		white-space: nowrap;
		font-family: 'Courier New', monospace;
		font-weight: 500;
		color: #34d399;
	}

	.data-table td.ric-cell-clickable {
		cursor: pointer;
	}

	.data-table td.ric-cell-clickable:hover {
		text-decoration: underline;
	}

	.data-table tbody tr:hover {
		background-color: #1f2937;
	}

	.data-table tbody tr.clickable-row {
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.data-table tbody tr.clickable-row:hover {
		background-color: #374151;
	}

	.data-table tbody tr.clickable-row:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: -2px;
	}

	.data-table tbody tr:last-child td {
		border-bottom: none;
	}

	.cell {
		font-size: 0.8125rem;
		vertical-align: top;
	}

	.empty-value {
		color: #6b7280;
		font-style: italic;
	}

	.info-message {
		margin-top: 2rem;
		padding: 1.5rem;
		background-color: #1e3a5f;
		border: 1px solid #10b981;
		border-radius: 0.5rem;
		color: #93c5fd;
		text-align: center;
	}
</style>

