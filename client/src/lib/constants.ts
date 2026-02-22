import config from './config.json';
import type { Exchange } from './types';

export interface AppConfig {
	api: {
		baseUrl: string;
		endpoints: {
			validateStock: string;
			validateFuture: string;
			validateOption: string;
			validateMultileg: string;
			validateCustom: string;
			validateByMasterId: string;
			rules: string;
			rulesFuture: string;
			rulesOption: string;
			rulesMultileg: string;
			rulesYaml: string;
			combinedRuleNames: string;
			combinedRuleDetails: string;
			combinedRuleDetailsYaml: string;
			instrumentsByExchange: string;
			instrumentsByExchangeFilter: string;
			instrumentById: string;
			instrumentByRic: string;
			exchanges: string;
			validationGlobalView: string;
			validationHeatmap: string;
			validationTreemap: string;
			validationRuleFailures: string;
			validationRuleFailuresByRegion: string;
			validationExpectationFailuresByRegion: string;
			validationCombinedRule: string;
			validationExchangeResults: string;
			validationRegionalTrends: string;
			validationRegionDateResults: string;
			validationRunSessions: string;
			excelReport: string;
		};
	};
	exchanges: Exchange[];
	defaultExchange: string;
}

export const APP_CONFIG: AppConfig = config as AppConfig;

export const API_BASE_URL = APP_CONFIG.api.baseUrl;
export const API_ENDPOINTS = APP_CONFIG.api.endpoints;
export const EXCHANGES: Exchange[] = APP_CONFIG.exchanges;
export const DEFAULT_EXCHANGE = APP_CONFIG.defaultExchange;

