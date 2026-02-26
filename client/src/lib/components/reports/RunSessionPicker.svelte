<script lang="ts">
	import { tick } from 'svelte';
	import type { RunSession } from '$lib/services/api';
	import Tooltip from '$lib/components/ui/Tooltip.svelte';

	interface Props {
		sessions: RunSession[];
		selectedSession: string;
		loading: boolean;
		onSelect: (sessionTime: string) => void;
	}

	let { sessions, selectedSession, loading, onSelect }: Props = $props();

	// ── Scroll track ──────────────────────────────────────────────
	let scrollEl = $state<HTMLDivElement | null>(null);
	let canScrollLeft  = $state(false);
	let canScrollRight = $state(false);

	function updateScrollState() {
		if (!scrollEl) return;
		canScrollLeft  = scrollEl.scrollLeft > 4;
		canScrollRight = scrollEl.scrollLeft + scrollEl.clientWidth < scrollEl.scrollWidth - 4;
	}

	function scroll(dir: 'left' | 'right') {
		if (!scrollEl) return;
		scrollEl.scrollBy({ left: dir === 'right' ? 220 : -220, behavior: 'smooth' });
	}

	// Scroll the active tab into view when it changes
	$effect(() => {
		if (!selectedSession || !scrollEl) return;
		tick().then(() => {
			const active = scrollEl?.querySelector('[aria-selected="true"]') as HTMLElement | null;
			active?.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' });
			updateScrollState();
		});
	});

	// Recheck overflow whenever sessions list changes
	$effect(() => {
		sessions; // track
		tick().then(updateScrollState);
	});

	function fmtTime(iso: string) {
		if (!iso) return '—';
		return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
	}
</script>

{#if sessions.length > 0}
	<div class="picker">
		<!-- Label + count -->
		<div class="picker-left">
			<svg viewBox="0 0 20 20" fill="currentColor" width="13" height="13">
				<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
			</svg>
			<span class="picker-label">Run</span>
			<span class="session-count">{sessions.length}</span>
		</div>

		<!-- Scroll left -->
		<button
			type="button"
			class="scroll-btn {!canScrollLeft ? 'hidden' : ''}"
			onclick={() => scroll('left')}
			aria-label="Scroll left"
			tabindex="-1"
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
			</svg>
		</button>

		<!-- Scrollable tab strip -->
		<div
			class="scroll-track"
			bind:this={scrollEl}
			onscroll={updateScrollState}
			role="tablist"
			aria-label="Run sessions"
		>
			{#each sessions as session (session.session_time)}
				{@const isActive = session.session_time === selectedSession}
				<button
					type="button"
					role="tab"
					aria-selected={isActive}
					class="session-tab {isActive ? 'active' : ''}"
					disabled={loading}
					onclick={() => onSelect(session.session_time)}
					title="{session.total_runs} exchange runs — {session.passed_runs} passed, {session.failed_runs} failed"
				>
					<span class="tab-time">{fmtTime(session.session_time)}</span>
					<span class="tab-badges">
						{#if session.failed_runs > 0}
							<Tooltip text="{session.failed_runs} exchange{session.failed_runs !== 1 ? 's' : ''} failed" placement="bottom">
								<span class="badge fail">{session.failed_runs}✗</span>
							</Tooltip>
						{/if}
						{#if session.passed_runs > 0}
							<Tooltip text="{session.passed_runs} exchange{session.passed_runs !== 1 ? 's' : ''} passed" placement="bottom">
								<span class="badge pass">{session.passed_runs}✓</span>
							</Tooltip>
						{/if}
					</span>
				</button>
			{/each}
		</div>

		<!-- Scroll right -->
		<button
			type="button"
			class="scroll-btn {!canScrollRight ? 'hidden' : ''}"
			onclick={() => scroll('right')}
			aria-label="Scroll right"
			tabindex="-1"
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
			</svg>
		</button>

		<!-- Position indicator for many sessions -->
		{#if sessions.length > 6}
			<span class="position-hint">
				{sessions.findIndex(s => s.session_time === selectedSession) + 1} / {sessions.length}
			</span>
		{/if}
	</div>
{/if}

<style>
	.picker {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #0d1117;
		border: 1px solid #1f2937;
		border-radius: 0.5rem;
		padding: 0.3rem 0.625rem;
		margin-bottom: 0.625rem;
		min-width: 0;
	}

	/* ── Left label group ─────────────────────────────────────── */
	.picker-left {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		flex-shrink: 0;
		color: #6b7280;
	}

	.picker-label {
		font-size: 0.6875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		white-space: nowrap;
	}

	.session-count {
		font-size: 0.6875rem;
		font-weight: 700;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 9999px;
		color: #9ca3af;
		padding: 0.05rem 0.45rem;
		line-height: 1.4;
	}

	/* ── Scroll arrows ────────────────────────────────────────── */
	.scroll-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		width: 1.5rem;
		height: 1.5rem;
		padding: 0;
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.25rem;
		color: #9ca3af;
		cursor: pointer;
		transition: all 0.15s;
	}

	.scroll-btn:hover {
		background: #374151;
		color: #e5e7eb;
		border-color: var(--color-primary);
	}

	.scroll-btn.hidden {
		visibility: hidden;
		pointer-events: none;
	}

	.scroll-btn svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	/* ── Scrollable strip ─────────────────────────────────────── */
	.scroll-track {
		display: flex;
		gap: 0.375rem;
		overflow-x: auto;
		scroll-snap-type: x proximity;
		/* hide scrollbar but keep scrollable */
		scrollbar-width: none;
		-ms-overflow-style: none;
		flex: 1;
		min-width: 0;
		padding: 2px 0; /* so focus rings aren't clipped */
	}

	.scroll-track::-webkit-scrollbar {
		display: none;
	}

	/* ── Individual session tab ───────────────────────────────── */
	.session-tab {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		background: #111827;
		border: 1px solid #374151;
		border-radius: 0.375rem;
		color: #9ca3af;
		font-size: 0.75rem;
		padding: 0.2rem 0.5rem;
		cursor: pointer;
		transition: all 0.15s;
		white-space: nowrap;
		flex-shrink: 0;
		scroll-snap-align: start;
	}

	.session-tab:hover:not(:disabled):not(.active) {
		background: #1f2937;
		border-color: var(--color-primary);
		color: #e5e7eb;
	}

	.session-tab.active {
		background: #1e3a5f;
		border-color: #2563a8;
		color: #93c5fd;
		font-weight: 600;
	}

	.session-tab:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.tab-time {
		font-variant-numeric: tabular-nums;
	}

	.tab-badges {
		display: flex;
		gap: 0.25rem;
	}

	.badge {
		font-size: 0.6rem;
		font-weight: 700;
		padding: 0.1rem 0.3rem;
		border-radius: 0.25rem;
		letter-spacing: 0.02em;
		font-variant-numeric: tabular-nums;
	}

	.badge.fail {
		background: rgba(239, 68, 68, 0.15);
		color: #f87171;
		border: 1px solid rgba(239, 68, 68, 0.3);
	}

	.badge.pass {
		background: rgba(52, 211, 153, 0.12);
		color: #34d399;
		border: 1px solid rgba(52, 211, 153, 0.25);
	}

	/* ── Position indicator ───────────────────────────────────── */
	.position-hint {
		flex-shrink: 0;
		font-size: 0.6875rem;
		color: #4b5563;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
</style>
