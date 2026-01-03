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

export interface Exchange {
	value: string;
	label: string;
}

export interface TableData {
	data: Array<Record<string, any>>;
	headers: string[];
}

