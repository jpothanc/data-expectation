# Chart Components

This directory contains reusable chart components for visualizing data across the application.

## Components

### ChartCard

A container component for charts with title and statistics.

**Usage:**
```svelte
<script>
  import ChartCard from '$lib/components/ChartCard.svelte';
  
  const stats = [
    { label: 'Total', value: 100 },
    { label: 'Passed', value: 75, highlight: 'success' },
    { label: 'Failed', value: 25, highlight: 'failed' }
  ];
</script>

<ChartCard title="Exchange Name" stats={stats}>
  <!-- Chart component here -->
</ChartCard>
```

**Props:**
- `title` (string): Card title
- `stats` (Array, optional): Array of statistics to display
- `children`: Chart component to render inside

## Utilities

### Validation Utilities (`src/lib/utils/validation.ts`)

- `getPassFailCounts()`: Extracts pass/fail counts from validation response data
