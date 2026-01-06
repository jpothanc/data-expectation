import { API_BASE_URL, API_ENDPOINTS } from '../constants';
import { extractInstruments } from '../utils/table';
import type { ValidationResponse, Exchange } from '../types';

/**
 * Helper function to create a fetch request with timeout and error handling
 */
async function apiRequest<T>(
	endpoint: string,
	options: RequestInit = {},
	timeoutMs: number = 30000
): Promise<T> {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
	
	try {
		const response = await fetch(`${API_BASE_URL}${endpoint}`, {
			...options,
			signal: controller.signal
		});
		
		clearTimeout(timeoutId);
		
		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}
		
		return await response.json();
	} catch (err) {
		clearTimeout(timeoutId);
		if (err instanceof Error && err.name === 'AbortError') {
			throw new Error(`Request timeout after ${timeoutMs}ms`);
		}
		throw err;
	}
}

export async function validateStocks(exchange: string): Promise<ValidationResponse> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validateStock}/${exchange}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function validateFutures(exchange: string): Promise<ValidationResponse> {
	const url = `${API_BASE_URL}/api/v1/rules/validate/future/${exchange}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function validateOptions(exchange: string): Promise<ValidationResponse> {
	const url = `${API_BASE_URL}/api/v1/rules/validate/option/${exchange}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function validateCustom(
	instrumentType: string,
	exchange: string,
	customRuleNames: string[]
): Promise<ValidationResponse> {
	// Build query parameters for custom rule names
	const queryParams = customRuleNames.map(name => `custom_rule_names=${encodeURIComponent(name)}`).join('&');
	const url = `${API_BASE_URL}${API_ENDPOINTS.validateCustom}/${instrumentType}/${exchange}?${queryParams}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function validateCombinedRule(
	instrumentType: string,
	exchange: string,
	combinedRuleName: string
): Promise<ValidationResponse> {
	// Use the validateCustom endpoint with combined rule name
	// Combined rules are validated the same way as custom rules
	const url = `${API_BASE_URL}${API_ENDPOINTS.validateCustom}/${instrumentType}/${exchange}?custom_rule_names=${encodeURIComponent(combinedRuleName)}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getInstrumentsByExchange(exchange: string, productType: string = 'stock'): Promise<any[]> {
	const endpoint = `${API_ENDPOINTS.instrumentsByExchange}/${exchange}`;
	const url = `${API_BASE_URL}${endpoint}?product_type=${productType}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	const result = await response.json();
	return extractInstruments(result);
}

export async function getInstrumentById(instrumentId: string, exchange?: string, productType: string = 'stock'): Promise<any[]> {
	const endpoint = `${API_ENDPOINTS.instrumentById}/${encodeURIComponent(instrumentId)}`;
	let url = `${API_BASE_URL}${endpoint}?product_type=${productType}`;
	if (exchange) {
		url += `&exchange=${encodeURIComponent(exchange)}`;
	}
	
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	const result = await response.json();
	return extractInstruments(result);
}

export async function getInstrumentByRic(ric: string, exchange?: string, productType: string = 'stock'): Promise<any[]> {
	const endpoint = `${API_ENDPOINTS.instrumentByRic}/${encodeURIComponent(ric)}`;
	let url = `${API_BASE_URL}${endpoint}?product_type=${productType}`;
	if (exchange) {
		url += `&exchange=${encodeURIComponent(exchange)}`;
	}
	
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	const result = await response.json();
	return extractInstruments(result);
}

export async function getRules(exchange: string, productType: string = 'stock'): Promise<any> {
	const endpoint = productType === 'stock'
		? `${API_ENDPOINTS.rules}/${exchange}`
		: productType === 'future'
		? `/api/v1/rules/rules/futures/${exchange}`
		: `/api/v1/rules/rules/options/${exchange}`;
	
	const url = `${API_BASE_URL}${endpoint}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getRulesYaml(
	productType: string,
	exchange: string
): Promise<string> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.rulesYaml}/${productType}/${exchange}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.text();
}

export async function getCombinedRuleDetailsYaml(
	productType: string,
	exchange: string,
	ruleName?: string
): Promise<string> {
	let url = `${API_BASE_URL}${API_ENDPOINTS.combinedRuleDetailsYaml}/${productType}/${exchange}`;
	if (ruleName) {
		url += `?rule_name=${encodeURIComponent(ruleName)}`;
	}
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.text();
}

export async function validateByMasterId(
	masterId: string,
	ruleName: string
): Promise<ValidationResponse> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validateByMasterId}/${masterId}/${ruleName}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getExchanges(productType: string = 'stock'): Promise<Exchange[]> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.exchanges}?product_type=${productType}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	const result = await response.json();
	
	// API now returns simple array of strings: ["XHKG", "XNSE", ...]
	if (Array.isArray(result)) {
		return result.map((item: string) => ({
			value: item,
			label: item
		}));
	}
	
	return [];
}

export async function getCombinedRuleNames(
	instrumentType: string,
	exchange: string
): Promise<string[]> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.combinedRuleNames}/${instrumentType}/${exchange}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	const result = await response.json();
	
	// Handle the API response format: { all_combined_rule_names: [...], ... } or { combined_rule_names: [...], ... }
	if (result && Array.isArray(result.all_combined_rule_names)) {
		return result.all_combined_rule_names;
	}
	if (result && Array.isArray(result.combined_rule_names)) {
		return result.combined_rule_names;
	}
	
	// Fallback for other formats
	if (Array.isArray(result)) {
		return result.map((item: any) => typeof item === 'string' ? item : item.name || item.ruleName || String(item));
	} else if (result && Array.isArray(result.ruleNames)) {
		return result.ruleNames;
	} else if (result && Array.isArray(result.rules)) {
		return result.rules.map((item: any) => typeof item === 'string' ? item : item.name || item.ruleName || String(item));
	} else if (result && typeof result === 'object') {
		// If it's an object, try to extract rule names
		if (result.names && Array.isArray(result.names)) {
			return result.names;
		}
		return Object.keys(result).filter(key => 
			result[key] && typeof result[key] === 'string'
		);
	}
	
	return [];
}

export async function getCombinedRuleDetails(
	instrumentType: string,
	exchange: string,
	ruleName: string
): Promise<any> {
	// Use the combined-rules-details endpoint
	const url = `${API_BASE_URL}${API_ENDPOINTS.combinedRuleDetails}/${instrumentType}/${exchange}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	const combinedRuleData = await response.json();
	
	// The API returns: { product_type, exchange, combined_rules: [...], count }
	// Each combined_rule has: { name, definition, includes, resolved_rules: [...], ... }
	
	if (!combinedRuleData || !Array.isArray(combinedRuleData.combined_rules)) {
		return [];
	}
	
	// Find the specific combined rule by name
	const specificRule = combinedRuleData.combined_rules.find(
		(rule: any) => rule.name === ruleName || rule.ruleName === ruleName
	);
	
	if (!specificRule) {
		return [];
	}
	
	// Extract resolved_rules from the combined rule
	// resolved_rules contains the actual rule definitions that make up the combined rule
	if (Array.isArray(specificRule.resolved_rules) && specificRule.resolved_rules.length > 0) {
		return specificRule.resolved_rules;
	}
	
	// If resolved_rules is empty or not an array, log for debugging
	if (!Array.isArray(specificRule.resolved_rules)) {
		console.warn('resolved_rules is not an array:', specificRule.resolved_rules);
	}
	
	// Fallback: if resolved_rules is not available, try to use includes or other fields
	if (Array.isArray(specificRule.includes)) {
		// If we have includes (rule names), fetch the actual rules
		const allRules = await getRules(exchange, instrumentType);
		
		// Convert allRules to an array format
		let allRulesArray: any[] = [];
		if (Array.isArray(allRules)) {
			allRulesArray = allRules;
		} else if (allRules && typeof allRules === 'object') {
			if (Array.isArray(allRules.rules)) {
				allRulesArray = allRules.rules;
			} else if (Array.isArray(allRules.data)) {
				allRulesArray = allRules.data;
			} else {
				allRulesArray = [allRules];
			}
		}
		
		// Filter rules to only include those that are part of the combined rule
		const filteredRules = allRulesArray.filter((rule: any) => {
			const ruleNameToMatch = rule.name || rule.ruleName || rule.rule_name || String(rule);
			return specificRule.includes.some((name: string) => 
				name.toLowerCase() === ruleNameToMatch.toLowerCase()
			);
		});
		
		return filteredRules;
	}
	
	// Last resort: return the combined rule object itself
	return [specificRule];
}

// Validation Analytics API functions

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

export async function getGlobalView(days: number = 7): Promise<{ data: GlobalViewData[]; chart_type: string; chart_title: string }> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validationGlobalView}?days=${days}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getHeatmap(days: number = 7): Promise<{ data: HeatmapData[]; chart_type: string; chart_title: string }> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validationHeatmap}?days=${days}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getTreemap(days: number = 7): Promise<{ data: TreemapData[]; chart_type: string; chart_title: string }> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validationTreemap}?days=${days}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getRuleFailures(days: number = 7, limit: number = 20): Promise<{ data: RuleFailureData[]; chart_type: string; chart_title: string }> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validationRuleFailures}?days=${days}&limit=${limit}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getCombinedRuleStats(combinedRuleName: string, days: number = 7): Promise<CombinedRuleData> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validationCombinedRule}/${encodeURIComponent(combinedRuleName)}?days=${days}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
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
	expectation_results: Array<{
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
	}>;
	rules_applied: Array<{
		RuleName: string;
		RuleType: string;
		RuleLevel: string;
		RuleSource: string;
	}>;
}

export interface ExchangeValidationResponse {
	exchange: string;
	days: number;
	total_runs: number;
	runs: ExchangeValidationResult[];
}

export async function getExchangeValidationResults(
	exchange: string,
	days: number = 7,
	limit?: number,
	signal?: AbortSignal
): Promise<ExchangeValidationResponse> {
	let url = `${API_BASE_URL}${API_ENDPOINTS.validationExchangeResults}/${encodeURIComponent(exchange)}?days=${days}`;
	if (limit) {
		url += `&limit=${limit}`;
	}
	
	const fetchOptions: RequestInit = {};
	if (signal) {
		fetchOptions.signal = signal;
	}
	
	const response = await fetch(url, fetchOptions);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

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
	data: Record<string, RegionalTrendData[]>; // Key is region name (e.g., "APAC", "US", "EMEA")
	chart_type: string;
	chart_title: string;
}

export async function getRegionalTrends(days: number = 30): Promise<RegionalTrendResponse> {
	const url = `${API_BASE_URL}${API_ENDPOINTS.validationRegionalTrends}?days=${days}`;
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

export async function getValidationResultsByRegionDate(
	region: string,
	date: string,
	days: number = 7,
	limit?: number
): Promise<ExchangeValidationResponse> {
	let url = `${API_BASE_URL}${API_ENDPOINTS.validationRegionDateResults}/${encodeURIComponent(region)}/${encodeURIComponent(date)}?days=${days}`;
	if (limit) {
		url += `&limit=${limit}`;
	}
	
	const response = await fetch(url);
	
	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}
	
	return await response.json();
}

