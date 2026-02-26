<script lang="ts">
	import { onMount } from 'svelte';
	import { getRulesYaml } from '$lib/services/api';

	interface RuleApplied {
		RuleName: string;
		RuleType: string;
		RuleLevel: string;
		RuleSource: string;
	}

	interface Props {
		rule: RuleApplied;
		exchange: string;
		productType: string;
		onClose: () => void;
	}

	let { rule, exchange, productType, onClose }: Props = $props();

	let yaml = $state('');
	let loading = $state(true);
	let error = $state<string | null>(null);
	let copied = $state(false);

	onMount(async () => {
		try {
			yaml = await getRulesYaml(productType, exchange);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load rules YAML';
		} finally {
			loading = false;
		}
	});

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(yaml);
			copied = true;
			setTimeout(() => {
				copied = false;
			}, 2000);
		} catch {
			// clipboard not available
		}
	}

	function handleOverlayKey(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}

	/**
	 * Minimal YAML syntax highlighter — no external deps.
	 * Escapes HTML first, then wraps tokens in <span> elements.
	 * Lines containing the selected rule name get a highlight mark.
	 */
	function highlightYaml(src: string): string {
		const ruleNameLower = rule.RuleName.toLowerCase();
		return src
			.split('\n')
			.map((raw) => {
				// 1. Escape HTML characters
				const line = raw
					.replace(/&/g, '&amp;')
					.replace(/</g, '&lt;')
					.replace(/>/g, '&gt;');

				// 2. Blank lines
				if (!line.trim()) return line;

				// 3. Comment lines (# ...)
				if (line.trimStart().startsWith('#')) {
					return `<span class="y-comment">${line}</span>`;
				}

				// 4. Key: value — capture leading indent + optional dash, then key, then colon + rest
				const kvMatch = line.match(/^(\s*(?:-\s+)?)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:.*)$/);
				if (kvMatch) {
					const [, indent, key, rest] = kvMatch;
					// Color the value part after the colon
					const coloredRest = rest.replace(
						/^(\s*:\s*)(.+)?$/,
						(_, colon, val) =>
							val ? `${colon}<span class="y-value">${val}</span>` : colon
					);
					return `${indent}<span class="y-key">${key}</span>${coloredRest}`;
				}

				// 5. List item "  - somevalue"
				const liMatch = line.match(/^(\s*)(-)(\s+.+)$/);
				if (liMatch) {
					const [, indent, dash, rest] = liMatch;
					return `${indent}<span class="y-dash">${dash}</span><span class="y-list-val">${rest}</span>`;
				}

				return line;
			})
			.map((line) => {
				// Highlight every line that contains the rule name
				if (ruleNameLower && line.toLowerCase().includes(ruleNameLower)) {
					return `<span class="y-match">${line}</span>`;
				}
				return line;
			})
			.join('\n');
	}

	const highlighted = $derived(yaml ? highlightYaml(yaml) : '');
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
	class="overlay"
	role="dialog"
	aria-modal="true"
	aria-label="Rule YAML viewer"
	onclick={onClose}
	onkeydown={handleOverlayKey}
>
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div class="modal" role="document" onclick={(e) => e.stopPropagation()} onkeydown={() => {}}>
		<!-- Header -->
		<div class="modal-header">
			<div class="header-left">
				<h2>Rule Details — YAML</h2>
				<div class="header-meta">
					<span class="badge exchange">{exchange}</span>
					<span class="badge product">{productType}</span>
					{#if rule.RuleSource}
						<span class="badge source" title={rule.RuleSource}>
							{rule.RuleSource}
						</span>
					{/if}
				</div>
			</div>
			<div class="header-actions">
				{#if !loading && !error && yaml}
					<button class="copy-btn" onclick={copyToClipboard} type="button">
						{#if copied}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
							Copied
						{:else}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
								/>
							</svg>
							Copy
						{/if}
					</button>
				{/if}
				<button class="close-btn" onclick={onClose} type="button" aria-label="Close">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
		</div>

		<!-- Rule info strip -->
		{#if !loading && !error}
			<div class="rule-strip">
				<div class="rule-strip-item">
					<span class="strip-label">Rule</span>
					<span class="strip-value rule-name">{rule.RuleName}</span>
				</div>
				{#if rule.RuleType}
					<div class="rule-strip-item">
						<span class="strip-label">Type</span>
						<span class="strip-value">{rule.RuleType}</span>
					</div>
				{/if}
				{#if rule.RuleLevel}
					<div class="rule-strip-item">
						<span class="strip-label">Level</span>
						<span class="strip-value">{rule.RuleLevel}</span>
					</div>
				{/if}
				<div class="strip-hint">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10" />
						<path stroke-linecap="round" d="M12 8v4M12 16h.01" />
					</svg>
					Matching lines are highlighted
				</div>
			</div>
		{/if}

		<!-- Body -->
		<div class="modal-body">
			{#if loading}
				<div class="state-msg">
					<span class="spinner"></span>
					Loading YAML…
				</div>
			{:else if error}
				<div class="state-msg error">{error}</div>
			{:else}
				<pre class="yaml-block">{@html highlighted}</pre>
			{/if}
		</div>
	</div>
</div>

<style>
	/* ── Overlay ──────────────────────────────────────────────── */
	.overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10100;
		padding: 1rem;
	}

	/* ── Modal ────────────────────────────────────────────────── */
	.modal {
		background: #111827;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		width: min(820px, 95vw);
		max-height: 85vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6);
		overflow: hidden;
	}

	/* ── Header ───────────────────────────────────────────────── */
	.modal-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.875rem 1.25rem;
		border-bottom: 1px solid #1f2937;
		flex-shrink: 0;
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		min-width: 0;
	}

	.modal-header h2 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #fff;
	}

	.header-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		align-items: center;
	}

	.badge {
		padding: 0.15rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.6875rem;
		font-weight: 500;
		white-space: nowrap;
	}

	.badge.exchange {
		background: #1e3a5f;
		color: #60a5fa;
		border: 1px solid #1e40af;
	}

	.badge.product {
		background: #1f2937;
		color: #9ca3af;
		border: 1px solid #374151;
		text-transform: uppercase;
	}

	.badge.source {
		background: #1f2937;
		color: #6b7280;
		border: 1px solid #374151;
		font-family: monospace;
		max-width: 280px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.copy-btn {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #d1d5db;
		font-size: 0.8125rem;
		padding: 0.35rem 0.75rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.copy-btn:hover {
		background: #374151;
		color: #fff;
	}

	.copy-btn svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		cursor: pointer;
		width: 2rem;
		height: 2rem;
		padding: 0;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.close-btn:hover {
		background: #374151;
		color: #fff;
		border-color: var(--color-primary);
	}

	.close-btn svg {
		width: 1rem;
		height: 1rem;
	}

	/* ── Rule info strip ──────────────────────────────────────── */
	.rule-strip {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 1.25rem;
		padding: 0.625rem 1.25rem;
		background: #0d1117;
		border-bottom: 1px solid #1f2937;
		flex-shrink: 0;
	}

	.rule-strip-item {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	.strip-label {
		font-size: 0.6875rem;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.strip-value {
		font-size: 0.8125rem;
		color: #e5e7eb;
		font-weight: 500;
	}

	.strip-value.rule-name {
		color: var(--color-primary-light);
		font-family: monospace;
	}

	.strip-hint {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.6875rem;
		color: #4b5563;
		margin-left: auto;
	}

	.strip-hint svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	/* ── Modal body / YAML block ──────────────────────────────── */
	.modal-body {
		overflow-y: auto;
		flex: 1;
		scrollbar-width: thin;
		scrollbar-color: var(--color-primary-dark) #0d1117;
	}

	.modal-body::-webkit-scrollbar {
		width: 8px;
	}

	.modal-body::-webkit-scrollbar-track {
		background: #0d1117;
	}

	.modal-body::-webkit-scrollbar-thumb {
		background: var(--color-primary-dark);
		border-radius: 4px;
	}

	.yaml-block {
		margin: 0;
		padding: 1rem 1.25rem;
		font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
		font-size: 0.75rem;
		line-height: 1.7;
		color: #e5e7eb;
		background: #0d1117;
		overflow-x: auto;
		tab-size: 2;
		white-space: pre;
	}

	/* ── YAML token colours (applied via {@html}) ─────────────── */
	:global(.y-comment) {
		color: #6b7280;
		font-style: italic;
	}

	:global(.y-key) {
		color: #60a5fa;
		font-weight: 600;
	}

	:global(.y-value) {
		color: #a3e635;
	}

	:global(.y-dash) {
		color: #f59e0b;
	}

	:global(.y-list-val) {
		color: #e5e7eb;
	}

	:global(.y-match) {
		display: block;
		background: rgba(250, 204, 21, 0.08);
		border-left: 3px solid #facc15;
		padding-left: 0.25rem;
		margin-left: -0.25rem;
	}

	/* ── State messages ───────────────────────────────────────── */
	.state-msg {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		padding: 3rem;
		color: #9ca3af;
		font-size: 0.9375rem;
	}

	.state-msg.error {
		color: #f87171;
	}

	.spinner {
		width: 1.25rem;
		height: 1.25rem;
		border: 2px solid #374151;
		border-top-color: var(--color-primary);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
