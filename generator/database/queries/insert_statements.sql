-- Example INSERT statements for validation results
-- These show how to insert data from the generator API responses
-- SQL Server compatible syntax

-- Use RubyUsers database
USE [RubyUsers];
GO

-- ============================================================================
-- Sample 1: APAC - XHKG Stock Validation (Failed)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp],
    [Region],
    [ProductType],
    [Exchange],
    [Success],
    [TotalExpectations],
    [SuccessfulExpectations],
    [FailedExpectations],
    [RulesApplied],
    [CustomRuleNames],
    [ApiUrl],
    [ExecutionDurationMs]
) VALUES (
    DATEADD(HOUR, -2, GETDATE()),
    N'apac',
    N'stock',
    N'XHKG',
    0,  -- false - validation failed
    22,
    19,
    3,
    N'combined',
    N'is_tradable_stocks,status_validation',
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XHKG',
    1250
);

DECLARE @RunId1 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId1, N'MasterId', N'ExpectColumnValuesToBeUnique', 0, 10, 2, 20.0, 0, 0.0, N'{"partial_unexpected_list": [1001, 1001], "partial_unexpected_counts": [{"value": 1001, "count": 2}]}'),
(@RunId1, N'MasterId', N'ExpectColumnValuesToNotBeNull', 1, 10, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId1, N'ISIN', N'ExpectColumnValuesToBeUnique', 1, 10, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId1, N'RIC', N'ExpectColumnValuesToNotBeNull', 0, 10, 1, 10.0, 0, 0.0, N'{"partial_unexpected_list": [null], "partial_unexpected_counts": [{"value": null, "count": 1}]}'),
(@RunId1, N'Currency', N'ExpectColumnValuesToBeInSet', 0, 10, 5, 50.0, 0, 0.0, N'{"partial_unexpected_list": ["HKD2", "HKD3", "4", "USD"], "partial_unexpected_counts": [{"value": "HKD2", "count": 2}, {"value": "4", "count": 1}]}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId1, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId1, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId1, N'xhkg_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xhkg/exchange.yaml'),
(@RunId1, N'is_tradable_stocks', N'combined', N'exchange', N'config/rules/stock/exchanges/xhkg/combined.yaml');

-- ============================================================================
-- Sample 2: APAC - XNSE Stock Validation (Successful)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(HOUR, -1, GETDATE()),
    N'apac',
    N'stock',
    N'XNSE',
    1,  -- true - validation successful
    20,
    20,
    0,
    N'base',
    NULL,
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XNSE',
    980
);

DECLARE @RunId2 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId2, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 15, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId2, N'ISIN', N'ExpectColumnValuesToBeUnique', 1, 15, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId2, N'RIC', N'ExpectColumnValuesToNotBeNull', 1, 15, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId2, N'Currency', N'ExpectColumnValuesToBeInSet', 1, 15, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId2, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId2, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId2, N'xnse_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xnse/exchange.yaml');

-- ============================================================================
-- Sample 3: EMEA - XLON Stock Validation (Failed)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(MINUTE, -30, GETDATE()),
    N'emea',
    N'stock',
    N'XLON',
    0,  -- false
    18,
    16,
    2,
    N'exchange',
    NULL,
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XLON',
    1100
);

DECLARE @RunId3 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId3, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 12, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId3, N'ISIN', N'ExpectColumnValuesToBeUnique', 0, 12, 1, 8.33, 0, 0.0, N'{"partial_unexpected_list": ["GB0002875804"], "partial_unexpected_counts": [{"value": "GB0002875804", "count": 2}]}'),
(@RunId3, N'RIC', N'ExpectColumnValuesToNotBeNull', 1, 12, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId3, N'Currency', N'ExpectColumnValuesToBeInSet', 0, 12, 2, 16.67, 0, 0.0, N'{"partial_unexpected_list": ["EUR", "EUR"], "partial_unexpected_counts": [{"value": "EUR", "count": 2}]}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId3, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId3, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId3, N'xlon_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xlon/exchange.yaml');

-- ============================================================================
-- Sample 4: US - XNYS Stock Validation (Successful)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(MINUTE, -15, GETDATE()),
    N'us',
    N'stock',
    N'XNYS',
    1,  -- true
    25,
    25,
    0,
    N'combined',
    N'comprehensive_validation',
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XNYS',
    1350
);

DECLARE @RunId4 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId4, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 20, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId4, N'ISIN', N'ExpectColumnValuesToBeUnique', 1, 20, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId4, N'Symbol', N'ExpectColumnValuesToNotBeNull', 1, 20, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId4, N'Currency', N'ExpectColumnValuesToBeInSet', 1, 20, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId4, N'SecurityType', N'ExpectColumnValuesToBeInSet', 1, 20, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId4, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId4, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId4, N'xnys_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xnys/exchange.yaml'),
(@RunId4, N'comprehensive_validation', N'combined', N'exchange', N'config/rules/stock/exchanges/xnys/combined.yaml');

-- ============================================================================
-- Sample 5: APAC - XTKS Stock Validation (Partial Failure)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(MINUTE, -5, GETDATE()),
    N'apac',
    N'stock',
    N'XTKS',
    0,  -- false
    21,
    20,
    1,
    N'custom',
    N'min_tradable_quantity_validation',
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XTKS',
    1050
);

DECLARE @RunId5 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId5, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 8, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId5, N'ISIN', N'ExpectColumnValuesToBeUnique', 1, 8, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId5, N'MinTradableQuantity', N'ExpectColumnValuesToBeBetween', 0, 8, 1, 12.5, 0, 0.0, N'{"partial_unexpected_list": [50], "partial_unexpected_counts": [{"value": 50, "count": 1}]}'),
(@RunId5, N'Currency', N'ExpectColumnValuesToBeInSet', 1, 8, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId5, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId5, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId5, N'xtks_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xtks/exchange.yaml'),
(@RunId5, N'min_tradable_quantity_validation', N'custom', N'exchange', N'config/rules/stock/exchanges/xtks/custom.yaml');

-- ============================================================================
-- Sample 6: Historical Data - APAC XHKG (1 day ago - Successful)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(DAY, -1, GETDATE()),
    N'apac',
    N'stock',
    N'XHKG',
    1,  -- true
    22,
    22,
    0,
    N'combined',
    N'is_tradable_stocks',
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XHKG',
    1180
);

DECLARE @RunId6 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId6, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 10, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId6, N'ISIN', N'ExpectColumnValuesToBeUnique', 1, 10, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId6, N'RIC', N'ExpectColumnValuesToNotBeNull', 1, 10, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId6, N'Currency', N'ExpectColumnValuesToBeInSet', 1, 10, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId6, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId6, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId6, N'xhkg_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xhkg/exchange.yaml'),
(@RunId6, N'is_tradable_stocks', N'combined', N'exchange', N'config/rules/stock/exchanges/xhkg/combined.yaml');

-- ============================================================================
-- Sample 7: EMEA - XPAR Stock Validation (Successful)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(HOUR, -3, GETDATE()),
    N'emea',
    N'stock',
    N'XPAR',
    1,  -- true
    19,
    19,
    0,
    N'base',
    NULL,
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XPAR',
    920
);

DECLARE @RunId7 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId7, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 14, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId7, N'ISIN', N'ExpectColumnValuesToBeUnique', 1, 14, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId7, N'RIC', N'ExpectColumnValuesToNotBeNull', 1, 14, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId7, N'Currency', N'ExpectColumnValuesToBeInSet', 1, 14, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId7, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId7, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId7, N'xpar_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xpar/exchange.yaml');

-- ============================================================================
-- Sample 8: US - XNAS Stock Validation (Failed)
-- ============================================================================
INSERT INTO [dbo].[GeValidationRuns] (
    [RunTimestamp], [Region], [ProductType], [Exchange],
    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
) VALUES (
    DATEADD(MINUTE, -45, GETDATE()),
    N'us',
    N'stock',
    N'XNAS',
    0,  -- false
    23,
    21,
    2,
    N'custom',
    N'nasdaq_listing_validation',
    N'http://127.0.0.1:5006/api/v1/rules/validate/stock/XNAS',
    1320
);

DECLARE @RunId8 BIGINT = SCOPE_IDENTITY();

INSERT INTO [dbo].[GeExpectationResults] (
    [RunId], [ColumnName], [ExpectationType], [Success],
    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
    [MissingCount], [MissingPercent], [ResultDetails]
) VALUES 
(@RunId8, N'MasterId', N'ExpectColumnValuesToBeUnique', 1, 18, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId8, N'Symbol', N'ExpectColumnValuesToNotBeNull', 0, 18, 1, 5.56, 0, 0.0, N'{"partial_unexpected_list": [null], "partial_unexpected_counts": [{"value": null, "count": 1}]}'),
(@RunId8, N'ISIN', N'ExpectColumnValuesToBeUnique', 0, 18, 1, 5.56, 0, 0.0, N'{"partial_unexpected_list": ["US0378331005"], "partial_unexpected_counts": [{"value": "US0378331005", "count": 2}]}'),
(@RunId8, N'Currency', N'ExpectColumnValuesToBeInSet', 1, 18, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}'),
(@RunId8, N'SecurityType', N'ExpectColumnValuesToBeInSet', 1, 18, 0, 0.0, 0, 0.0, N'{"partial_unexpected_list": [], "partial_unexpected_counts": []}');

INSERT INTO [dbo].[GeValidationRulesApplied] (
    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
) VALUES 
(@RunId8, N'base_rule_1', N'base', N'root', N'config/rules/base.yaml'),
(@RunId8, N'stock_rule_1', N'product_type', N'product_type', N'config/rules/stock/base.yaml'),
(@RunId8, N'xnas_exchange_rule_1', N'exchange', N'exchange', N'config/rules/stock/exchanges/xnas/exchange.yaml'),
(@RunId8, N'nasdaq_listing_validation', N'custom', N'exchange', N'config/rules/stock/exchanges/xnas/custom.yaml');

GO

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Uncomment to verify the inserts:
-- SELECT COUNT(*) as TotalRuns FROM [dbo].[GeValidationRuns];
-- SELECT Region, Exchange, Success, COUNT(*) as Count 
-- FROM [dbo].[GeValidationRuns] 
-- GROUP BY Region, Exchange, Success
-- ORDER BY Region, Exchange, Success;
-- 
-- SELECT TOP 10 * FROM [dbo].[GeValidationRuns] ORDER BY [RunTimestamp] DESC;
-- SELECT COUNT(*) as TotalExpectationResults FROM [dbo].[GeExpectationResults];
-- SELECT COUNT(*) as TotalRulesApplied FROM [dbo].[GeValidationRulesApplied];
