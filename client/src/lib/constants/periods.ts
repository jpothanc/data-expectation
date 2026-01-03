/**
 * Period options for analytics queries
 */
export interface PeriodOption {
	value: number;
	label: string;
}

export const PERIOD_OPTIONS: PeriodOption[] = [
	{ value: 7, label: '7 Days' },
	{ value: 14, label: '14 Days' },
	{ value: 30, label: '30 Days' },
	{ value: 60, label: '60 Days' },
	{ value: 90, label: '90 Days' }
] as const;

export const DEFAULT_PERIOD = 7;

