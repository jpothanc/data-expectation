<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		text: string;
		placement?: 'top' | 'bottom' | 'left' | 'right';
		children: Snippet;
	}

	let { text, placement = 'top', children }: Props = $props();
</script>

<span class="tooltip-wrap">
	{@render children()}
	<span class="tooltip {placement}" role="tooltip">{text}</span>
</span>

<style>
	.tooltip-wrap {
		position: relative;
		display: inline-flex;
		align-items: center;
	}

	/* ── Bubble ───────────────────────────────────────────────── */
	.tooltip {
		position: absolute;
		z-index: 9999;
		background: #1f2937;
		color: #e5e7eb;
		font-size: 0.6875rem;
		font-weight: 500;
		line-height: 1.3;
		white-space: nowrap;
		padding: 0.3rem 0.6rem;
		border-radius: 0.3rem;
		border: 1px solid #374151;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
		pointer-events: none;

		/* Hidden by default */
		opacity: 0;
		visibility: hidden;
		transition: opacity 0.15s, visibility 0.15s;
	}

	/* Arrow shared styles */
	.tooltip::after {
		content: '';
		position: absolute;
		border: 5px solid transparent;
	}

	/* ── Placement: top (default) ─────────────────────────────── */
	.tooltip.top {
		bottom: calc(100% + 7px);
		left: 50%;
		transform: translateX(-50%);
	}

	.tooltip.top::after {
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		border-top-color: #374151;
	}

	/* ── Placement: bottom ────────────────────────────────────── */
	.tooltip.bottom {
		top: calc(100% + 7px);
		left: 50%;
		transform: translateX(-50%);
	}

	.tooltip.bottom::after {
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%);
		border-bottom-color: #374151;
	}

	/* ── Placement: left ──────────────────────────────────────── */
	.tooltip.left {
		right: calc(100% + 7px);
		top: 50%;
		transform: translateY(-50%);
	}

	.tooltip.left::after {
		left: 100%;
		top: 50%;
		transform: translateY(-50%);
		border-left-color: #374151;
	}

	/* ── Placement: right ─────────────────────────────────────── */
	.tooltip.right {
		left: calc(100% + 7px);
		top: 50%;
		transform: translateY(-50%);
	}

	.tooltip.right::after {
		right: 100%;
		top: 50%;
		transform: translateY(-50%);
		border-right-color: #374151;
	}

	/* ── Show on hover / focus ────────────────────────────────── */
	.tooltip-wrap:hover .tooltip,
	.tooltip-wrap:focus-within .tooltip {
		opacity: 1;
		visibility: visible;
	}
</style>
