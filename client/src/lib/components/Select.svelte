<script lang="ts">
	interface Option {
		value: string;
		label: string;
	}

	interface Props {
		id?: string;
		value: string;
		options: Option[];
		disabled?: boolean;
		placeholder?: string;
		class?: string;
	}

	let { 
		id, 
		value = $bindable(), 
		options, 
		disabled = false, 
		placeholder,
		class: className = ''
	}: Props = $props();
</script>

<select 
	{id}
	bind:value
	{disabled}
	class="select {className}"
>
	{#if placeholder}
		<option value="" disabled>{placeholder}</option>
	{/if}
	{#each options as option}
		<option value={option.value}>{option.label}</option>
	{/each}
</select>

<style>
	.select {
		padding: 0.5rem 0.75rem;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		background-color: #1f2937;
		color: #e5e7eb;
		cursor: pointer;
		transition: border-color 0.2s, box-shadow 0.2s;
		min-width: 200px;
		height: 2.5rem;
		box-sizing: border-box;
	}

	.select:hover:not(:disabled) {
		border-color: #34d399;
	}

	.select:focus {
		outline: none;
		border-color: #34d399;
		box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
	}

	.select:disabled {
		background-color: #1f2937;
		cursor: not-allowed;
		color: #6b7280;
		opacity: 0.6;
	}

	.select option {
		background-color: #1f2937;
		color: #e5e7eb;
	}
</style>

