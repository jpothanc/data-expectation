// ─── Domain primitives ────────────────────────────────────────────────────────

export type ProductType = 'stock' | 'option' | 'future' | 'multileg';

export interface Exchange {
	value: string;
	label: string;
}

// ─── Validation (live run) ────────────────────────────────────────────────────

export interface ValidationResult {
	success: boolean;
	expectation_type?: string;
	column?: string;
	observed_value?: string;
	element_count?: number;
	result?: string;
}

export interface ValidationResponse {
	exchange?: string;
	success?: boolean;
	total_expectations?: number;
	successful_expectations?: number;
	failed_expectations?: number;
	results?: {
		expectation_results?: ValidationResult[];
		summary?: {
			success?: boolean;
			total?: number;
			successful?: number;
			failed?: number;
		};
	};
}

// ─── Rules ────────────────────────────────────────────────────────────────────

export interface Rule {
	name?: string;
	[key: string]: unknown;
}

export interface CombinedRuleDefinition {
	name: string;
	definition: Record<string, unknown>;
	includes: string[];
	resolved_rules: Rule[];
	resolved_rule_count?: number;
	full_rule_set_count?: number;
	base_and_exchange_rules_count?: number;
	error?: string;
}

export interface CombinedRulesResponse {
	product_type: string;
	exchange: string | null;
	combined_rules: CombinedRuleDefinition[];
	count: number;
}

// ─── Table ────────────────────────────────────────────────────────────────────

export interface TableData {
	data: Array<Record<string, string>>;
	headers: string[];
}

// ─── Analytics – generic chart wrapper ───────────────────────────────────────

export interface ChartResponse<T> {
	data: T[];
	chart_type: string;
	chart_title: string;
}

// ─── Analytics – data shapes ──────────────────────────────────────────────────

export interface GlobalViewData {
	Region: string;
	TotalRuns: number;
	SuccessfulRuns: number;
	FailedRuns: number;
	SuccessRate: number;
}

export interface HeatmapData {
	Region: string;
	ProductType: string;
	TotalRuns: number;
	SuccessfulRuns: number;
	SuccessRate: number;
}

export interface TreemapData {
	Region: string;
	ProductType: string;
	Exchange: string;
	TotalRuns: number;
	SuccessRate: number;
}

export interface RuleFailureData {
	RuleName: string;
	TotalRuns: number;
	FailureCount: number;
	FailureRate: number;
}

export interface RuleFailureByRegionData {
	Region: string;
	RuleName: string;
	TotalRuns: number;
	FailureCount: number;
	FailureRate: number;
}

export interface ExpectationFailureByRegionData {
	Region: string;
	ProductType: string;
	ColumnName: string;
	ExpectationType: string;
	TotalRuns: number;
	FailureCount: number;
	FailureRate: number;
}

export interface CombinedRuleData {
	TradableCount: number;
	NotTradableCount: number;
	TotalCount: number;
	TradableRate: number;
	FailureReasons: Array<{
		ColumnName: string;
		ExpectationType: string;
		FailureCount: number;
	}>;
	chart_type: string;
	chart_title: string;
}

// ─── Exchange validation history ──────────────────────────────────────────────

export interface ExpectationResult {
	ResultId: number;
	ColumnName: string;
	ExpectationType: string;
	Success: boolean;
	ElementCount: number;
	UnexpectedCount: number;
	UnexpectedPercent: number;
	MissingCount: number;
	MissingPercent: number;
	ResultDetails: string | null;
}

export interface RuleApplied {
	RuleName: string;
	RuleType: string;
	RuleLevel: string;
	RuleSource: string;
}

export interface ExchangeValidationResult {
	RunId: number;
	RunTimestamp: string;
	Region: string;
	ProductType: string;
	Exchange: string;
	Success: boolean;
	TotalExpectations: number;
	SuccessfulExpectations: number;
	FailedExpectations: number;
	RulesApplied: string;
	CustomRuleNames: string | null;
	ApiUrl: string;
	ExecutionDurationMs: number;
	expectation_results: ExpectationResult[];
	rules_applied: RuleApplied[];
}

/** Lightweight summary for a passed run — no sub-queries. */
export interface PassedExchangeRun {
	RunId: number;
	RunTimestamp: string;
	Exchange: string;
	ProductType: string;
	TotalExpectations: number;
	SuccessfulExpectations: number;
	ExecutionDurationMs: number;
	RulesApplied: number;
}

export interface ExchangeValidationResponse {
	exchange: string;
	days: number;
	total_runs: number;
	/** Failed runs — full detail including expectation results and rules applied. */
	runs: ExchangeValidationResult[];
	/** Passed runs — lightweight summary only. */
	passed_runs: PassedExchangeRun[];
}

// ─── Regional trends ──────────────────────────────────────────────────────────

export interface RegionalTrendData {
	Date: string;
	RunId?: number;
	Exchange?: string;
	ProductType?: string;
	Success?: number;
	FailedExpectations?: number;
	TotalExpectations?: number;
	SuccessfulExpectations?: number;
	TotalRuns?: number;
	SuccessfulRuns?: number;
	FailedRuns: number;
	SuccessRate: number;
}

export interface RegionalTrendResponse {
	/** Key is region name (e.g., "APAC", "US", "EMEA") */
	data: Record<string, RegionalTrendData[]>;
	chart_type: string;
	chart_title: string;
}

// ─── Run sessions ─────────────────────────────────────────────────────────────

export interface RunSession {
	/** ISO-8601 5-minute bucket start time */
	session_time: string;
	total_runs: number;
	passed_runs: number;
	failed_runs: number;
}

export interface RunSessionsResponse {
	region: string;
	date: string;
	sessions: RunSession[];
}
