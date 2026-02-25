<script lang="ts">
	interface Props {
		data: Array<{
			Region: string;
			ProductType: string;
			Exchange: string;
			TotalRuns: number;
			SuccessRate: number;
		}>;
		onExchangeClick?: (exchange: string) => void;
	}

	let { data, onExchangeClick }: Props = $props();

	// Group data by region and product type
	const treemapData = $derived.by(() => {
		const regions = [...new Set(data.map(d => d.Region))];
		const result: Record<string, Record<string, Array<{ exchange: string; rate: number }>>> = {};
		
		regions.forEach(region => {
			result[region] = {};
			const regionData = data.filter(d => d.Region === region);
			const productTypes = [...new Set(regionData.map(d => d.ProductType))];
			
			productTypes.forEach(productType => {
				const productData = regionData.filter(d => d.ProductType === productType);
				result[region][productType] = productData.map(d => {
					const rate = typeof d.SuccessRate === 'number' && !isNaN(d.SuccessRate) 
						? d.SuccessRate 
						: typeof d.SuccessRate === 'string' 
							? parseFloat(d.SuccessRate) || 0 
							: 0;
					return {
						exchange: d.Exchange,
						rate: rate
					};
				});
			});
		});
		
		return { regions, result };
	});

	function getColorClass(rate: number): string {
		if (rate >= 95) return 'excellent';
		if (rate >= 85) return 'good';
		if (rate >= 75) return 'fair';
		return 'poor';
	}
</script>

<div class="treemap-container">
	{#each treemapData.regions as region}
		<div class="region-section">
			<h3 class="region-title">{region}</h3>
			{#each Object.entries(treemapData.result[region]) as [productType, exchanges]}
				<div class="product-section">
					<h4 class="product-title">{productType.toUpperCase()}:</h4>
					<div class="exchanges-list">
						{#each exchanges as { exchange, rate }}
							{@const safeRate = typeof rate === 'number' && !isNaN(rate) ? rate : (typeof rate === 'string' ? parseFloat(rate) || 0 : 0)}
							{@const handleClick = (e: MouseEvent) => {
								e.preventDefault();
								e.stopPropagation();
								console.log('Exchange item clicked:', exchange, 'onExchangeClick:', onExchangeClick);
								if (onExchangeClick) {
									console.log('Calling onExchangeClick with:', exchange);
									onExchangeClick(exchange);
								} else {
									console.warn('onExchangeClick is not defined');
								}
							}}
							<div 
								class="exchange-item {getColorClass(safeRate)} {onExchangeClick ? 'clickable' : ''}"
								onclick={handleClick}
								onkeydown={(e) => {
									if ((e.key === 'Enter' || e.key === ' ') && onExchangeClick) {
										e.preventDefault();
										e.stopPropagation();
										onExchangeClick(exchange);
									}
								}}
								role={onExchangeClick ? 'button' : undefined}
								tabindex={onExchangeClick ? 0 : undefined}
								title={onExchangeClick ? `Click to view details for ${exchange}` : undefined}
							>
								<span class="exchange-name">{exchange}</span>
								<span class="exchange-rate">{safeRate.toFixed(0)}%</span>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/each}
</div>

<style>
	.treemap-container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.region-section {
		background-color: #1f2937;
		border: 1px solid #374151;
		border-radius: 0.5rem;
		padding: 1rem;
	}

	.region-title {
		margin: 0 0 1rem 0;
		font-size: 1.25rem;
		font-weight: 700;
		color: #34d399;
	}

	.product-section {
		margin-bottom: 1rem;
	}

	.product-section:last-child {
		margin-bottom: 0;
	}

	.product-title {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.exchanges-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.375rem;
	}

	.exchange-item {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 500;
		border: 1px solid;
		min-width: auto;
	}

	.exchange-item.excellent {
		background-color: #065f46;
		border-color: #047857;
		color: #d1fae5;
	}

	.exchange-item.good {
		background-color: #166534;
		border-color: #15803d;
		color: #bbf7d0;
	}

	.exchange-item.fair {
		background-color: #854d0e;
		border-color: #a16207;
		color: #fef3c7;
	}

	.exchange-item.poor {
		background-color: #991b1b;
		border-color: #b91c1c;
		color: #fecaca;
	}

	.exchange-item.clickable {
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.exchange-item.clickable:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
		opacity: 0.9;
	}

	.exchange-item.clickable:active {
		transform: translateY(0);
	}

	.exchange-name {
		font-weight: 600;
		font-size: 0.75rem;
	}

	.exchange-rate {
		font-size: 0.625rem;
		opacity: 0.9;
	}
</style>

