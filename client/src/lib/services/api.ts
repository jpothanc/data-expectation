import { API_BASE_URL, API_ENDPOINTS } from '../constants';
import { extractInstruments } from '../utils/table';
import type {
	ProductType,
	Exchange,
	ValidationResponse,
	ChartResponse,
	GlobalViewData,
	HeatmapData,
	TreemapData,
	RuleFailureData,
	RuleFailureByRegionData,
	ExpectationFailureByRegionData,
	CombinedRuleData,
	ExchangeValidationResponse,
	RegionalTrendResponse,
	RunSessionsResponse,
	CombinedRulesResponse,
	Rule,
} from '../types';

// ─── Structured API error ─────────────────────────────────────────────────────

export class ApiError extends Error {
	constructor(
		public readonly status: number,
		public readonly statusText: string,
		public readonly body = ''
	) {
		super(`HTTP ${status} ${statusText}${body ? `: ${body}` : ''}`);
		this.name = 'ApiError';
	}
}

// ─── Core HTTP transport ──────────────────────────────────────────────────────

const DEFAULT_TIMEOUT_MS = 30_000;

async function apiRequest<T>(
	endpoint: string,
	options: RequestInit = {},
	timeoutMs = DEFAULT_TIMEOUT_MS
): Promise<T> {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

	try {
		const response = await fetch(`${API_BASE_URL}${endpoint}`, {
			...options,
			// Caller-supplied signal takes precedence; fall back to timeout signal.
			signal: options.signal ?? controller.signal,
		});

		clearTimeout(timeoutId);

		if (!response.ok) {
			const body = await response.text().catch(() => '');
			throw new ApiError(response.status, response.statusText, body);
		}

		return response.json() as Promise<T>;
	} catch (err) {
		clearTimeout(timeoutId);
		if (err instanceof ApiError) throw err;
		if (err instanceof Error && err.name === 'AbortError') {
			throw new ApiError(408, 'Request Timeout', `Timed out after ${timeoutMs}ms`);
		}
		throw err;
	}
}

async function apiRequestText(endpoint: string, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<string> {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

	try {
		const response = await fetch(`${API_BASE_URL}${endpoint}`, {
			signal: controller.signal,
		});
		clearTimeout(timeoutId);
		if (!response.ok) {
			throw new ApiError(response.status, response.statusText);
		}
		return response.text();
	} catch (err) {
		clearTimeout(timeoutId);
		if (err instanceof ApiError) throw err;
		if (err instanceof Error && err.name === 'AbortError') {
			throw new ApiError(408, 'Request Timeout', `Timed out after ${timeoutMs}ms`);
		}
		throw err;
	}
}

// ─── URL builder ──────────────────────────────────────────────────────────────

/**
 * Builds a URL path with an optional query string.
 * `undefined` values are omitted; arrays produce repeated keys (e.g. multi-value params).
 */
function buildUrl(
	path: string,
	params?: Record<string, string | number | boolean | undefined>
): string {
	if (!params) return path;
	const qs = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined) qs.set(key, String(value));
	}
	const qsStr = qs.toString();
	return qsStr ? `${path}?${qsStr}` : path;
}

// ─── Validation (live run) ────────────────────────────────────────────────────

const VALIDATE_ENDPOINT: Record<ProductType, string> = {
	stock: API_ENDPOINTS.validateStock,
	option: API_ENDPOINTS.validateOption,
	future: API_ENDPOINTS.validateFuture,
	multileg: API_ENDPOINTS.validateMultileg,
};

export function validateExchange(
	productType: ProductType,
	exchange: string
): Promise<ValidationResponse> {
	return apiRequest<ValidationResponse>(`${VALIDATE_ENDPOINT[productType]}/${exchange}`);
}

// Convenience aliases kept for backwards-compatibility with existing call sites.
export const validateStocks = (exchange: string) => validateExchange('stock', exchange);
export const validateOptions = (exchange: string) => validateExchange('option', exchange);
export const validateFutures = (exchange: string) => validateExchange('future', exchange);
export const validateMultileg = (exchange: string) => validateExchange('multileg', exchange);

export function validateCustom(
	productType: string,
	exchange: string,
	customRuleNames: string[]
): Promise<ValidationResponse> {
	// URLSearchParams supports repeated keys for multi-value query params.
	const params = new URLSearchParams(
		customRuleNames.map((n) => ['custom_rule_names', n] as [string, string])
	);
	return apiRequest<ValidationResponse>(
		`${API_ENDPOINTS.validateCustom}/${productType}/${exchange}?${params}`
	);
}

export function validateCombinedRule(
	productType: string,
	exchange: string,
	combinedRuleName: string
): Promise<ValidationResponse> {
	return validateCustom(productType, exchange, [combinedRuleName]);
}

export function validateByMasterId(
	masterId: string,
	ruleName: string
): Promise<ValidationResponse> {
	return apiRequest<ValidationResponse>(
		`${API_ENDPOINTS.validateByMasterId}/${encodeURIComponent(masterId)}/${encodeURIComponent(ruleName)}`
	);
}

// ─── Instruments ──────────────────────────────────────────────────────────────

export async function getInstrumentsByExchange(
	exchange: string,
	productType: ProductType = 'stock'
): Promise<Record<string, unknown>[]> {
	const result = await apiRequest<unknown>(
		buildUrl(`${API_ENDPOINTS.instrumentsByExchange}/${exchange}`, { product_type: productType })
	);
	return extractInstruments(result);
}

export async function getInstrumentById(
	instrumentId: string,
	exchange?: string,
	productType: ProductType = 'stock'
): Promise<Record<string, unknown>[]> {
	const result = await apiRequest<unknown>(
		buildUrl(`${API_ENDPOINTS.instrumentById}/${encodeURIComponent(instrumentId)}`, {
			product_type: productType,
			exchange,
		})
	);
	return extractInstruments(result);
}

export async function getInstrumentByRic(
	ric: string,
	exchange?: string,
	productType: ProductType = 'stock'
): Promise<Record<string, unknown>[]> {
	const result = await apiRequest<unknown>(
		buildUrl(`${API_ENDPOINTS.instrumentByRic}/${encodeURIComponent(ric)}`, {
			product_type: productType,
			exchange,
		})
	);
	return extractInstruments(result);
}

// ─── Exchanges ────────────────────────────────────────────────────────────────

export async function getExchanges(productType: ProductType = 'stock'): Promise<Exchange[]> {
	const result = await apiRequest<string[] | unknown>(
		buildUrl(API_ENDPOINTS.exchanges, { product_type: productType })
	);
	if (!Array.isArray(result)) return [];
	return (result as string[]).map((item) => ({ value: item, label: item }));
}

// ─── Rules ────────────────────────────────────────────────────────────────────

const RULES_ENDPOINT: Record<ProductType, string> = {
	stock: API_ENDPOINTS.rules,
	future: API_ENDPOINTS.rulesFuture,
	option: API_ENDPOINTS.rulesOption,
	multileg: API_ENDPOINTS.rulesMultileg,
};

export function getRules(exchange: string, productType: ProductType = 'stock'): Promise<unknown> {
	return apiRequest<unknown>(`${RULES_ENDPOINT[productType]}/${exchange}`);
}

export function getRulesYaml(productType: string, exchange: string): Promise<string> {
	return apiRequestText(`${API_ENDPOINTS.rulesYaml}/${productType}/${exchange}`);
}

export function getCombinedRuleDetailsYaml(
	productType: string,
	exchange: string,
	ruleName?: string
): Promise<string> {
	return apiRequestText(
		buildUrl(`${API_ENDPOINTS.combinedRuleDetailsYaml}/${productType}/${exchange}`, {
			rule_name: ruleName,
		})
	);
}

export async function getCombinedRuleNames(
	productType: string,
	exchange: string
): Promise<string[]> {
	const result = await apiRequest<{ all_combined_rule_names?: string[] }>(
		`${API_ENDPOINTS.combinedRuleNames}/${productType}/${exchange}`
	);
	return result.all_combined_rule_names ?? [];
}

/**
 * Returns the full combined-rules payload for a product type / exchange.
 * Callers that need a single rule should filter on `combined_rules` by name.
 */
export function getCombinedRuleDetails(
	productType: string,
	exchange: string
): Promise<CombinedRulesResponse> {
	return apiRequest<CombinedRulesResponse>(
		`${API_ENDPOINTS.combinedRuleDetails}/${productType}/${exchange}`
	);
}

// ─── Validation analytics ─────────────────────────────────────────────────────

export function getGlobalView(days = 7): Promise<ChartResponse<GlobalViewData>> {
	return apiRequest<ChartResponse<GlobalViewData>>(
		buildUrl(API_ENDPOINTS.validationGlobalView, { days })
	);
}

export function getHeatmap(days = 7): Promise<ChartResponse<HeatmapData>> {
	return apiRequest<ChartResponse<HeatmapData>>(
		buildUrl(API_ENDPOINTS.validationHeatmap, { days })
	);
}

export function getTreemap(days = 7): Promise<ChartResponse<TreemapData>> {
	return apiRequest<ChartResponse<TreemapData>>(
		buildUrl(API_ENDPOINTS.validationTreemap, { days })
	);
}

export function getRuleFailures(days = 7, limit = 20): Promise<ChartResponse<RuleFailureData>> {
	return apiRequest<ChartResponse<RuleFailureData>>(
		buildUrl(API_ENDPOINTS.validationRuleFailures, { days, limit })
	);
}

export function getRuleFailuresByRegion(
	days = 7,
	limit = 20,
	productType?: string
): Promise<ChartResponse<RuleFailureByRegionData>> {
	return apiRequest<ChartResponse<RuleFailureByRegionData>>(
		buildUrl(API_ENDPOINTS.validationRuleFailuresByRegion, {
			days,
			limit,
			product_type: productType,
		})
	);
}

export function getExpectationFailuresByRegion(
	days = 7,
	limit = 20,
	productType?: string
): Promise<ChartResponse<ExpectationFailureByRegionData>> {
	return apiRequest<ChartResponse<ExpectationFailureByRegionData>>(
		buildUrl(API_ENDPOINTS.validationExpectationFailuresByRegion, {
			days,
			limit,
			product_type: productType,
		})
	);
}

export function getCombinedRuleStats(
	combinedRuleName: string,
	days = 7
): Promise<CombinedRuleData> {
	return apiRequest<CombinedRuleData>(
		buildUrl(
			`${API_ENDPOINTS.validationCombinedRule}/${encodeURIComponent(combinedRuleName)}`,
			{ days }
		)
	);
}

export function getExchangeValidationResults(
	exchange: string,
	days = 7,
	limit?: number,
	signal?: AbortSignal
): Promise<ExchangeValidationResponse> {
	return apiRequest<ExchangeValidationResponse>(
		buildUrl(
			`${API_ENDPOINTS.validationExchangeResults}/${encodeURIComponent(exchange)}`,
			{ days, limit }
		),
		{ signal }
	);
}

export function getRegionalTrends(
	days = 30,
	productType?: string
): Promise<RegionalTrendResponse> {
	return apiRequest<RegionalTrendResponse>(
		buildUrl(API_ENDPOINTS.validationRegionalTrends, { days, product_type: productType })
	);
}

export function getRunSessionsByRegionDate(
	region: string,
	date: string,
	days = 90
): Promise<RunSessionsResponse> {
	return apiRequest<RunSessionsResponse>(
		buildUrl(
			`${API_ENDPOINTS.validationRunSessions}/${encodeURIComponent(region)}/${encodeURIComponent(date)}`,
			{ days }
		)
	);
}

export function getValidationResultsByRegionDate(
	region: string,
	date: string,
	days = 7,
	limit?: number,
	sessionTime?: string
): Promise<ExchangeValidationResponse> {
	return apiRequest<ExchangeValidationResponse>(
		buildUrl(
			`${API_ENDPOINTS.validationRegionDateResults}/${encodeURIComponent(region)}/${encodeURIComponent(date)}`,
			{ days, limit, session_time: sessionTime }
		)
	);
}

/**
 * Returns the URL to download the consolidated Excel failure report.
 * Navigate to this URL directly to trigger the browser download.
 */
export function getExcelReportUrl(region: string, date: string, days = 90): string {
	return (
		API_BASE_URL +
		buildUrl(
			`${API_ENDPOINTS.excelReport}/${encodeURIComponent(region)}/${encodeURIComponent(date)}`,
			{ days }
		)
	);
}

// Re-export types that consumers may need alongside the API functions.
export type { Rule, CombinedRulesResponse };
