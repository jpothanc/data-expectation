-- Database schema for storing validation results and trends
-- Designed to support analytics, charts, and trending over time
-- SQL Server compatible syntax

-- ============================================================================
-- Create RubyUsers database if it doesn't exist
-- ============================================================================
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'RubyUsers')
BEGIN
    CREATE DATABASE [RubyUsers];
END
GO

-- Use RubyUsers database
USE [RubyUsers];
GO

-- ============================================================================
-- Main validation runs table
-- Stores metadata about each validation execution
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GeValidationRuns]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[GeValidationRuns] (
    [RunId] BIGINT PRIMARY KEY IDENTITY(1,1),
    [RunTimestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
    [Region] NVARCHAR(50) NOT NULL,
    [ProductType] NVARCHAR(50) NOT NULL,
    [Exchange] NVARCHAR(50) NOT NULL,
    
    -- Overall validation results
    [Success] BIT NOT NULL,
    [TotalExpectations] INT NOT NULL,
    [SuccessfulExpectations] INT NOT NULL,
    [FailedExpectations] INT NOT NULL,
    
    -- Rule configuration
    [RulesApplied] NVARCHAR(100) NULL, -- Type of rules: base, exchange, custom, combined
    [CustomRuleNames] NVARCHAR(MAX) NULL, -- Comma-separated list of custom rule names if applicable
    
    -- Metadata
    [ApiUrl] NVARCHAR(255) NULL,
    [ExecutionDurationMs] INT NULL -- Time taken to execute validation in milliseconds
);

CREATE INDEX [idx_RunTimestamp] ON [dbo].[GeValidationRuns] ([RunTimestamp]);
CREATE INDEX [idx_RegionExchange] ON [dbo].[GeValidationRuns] ([Region], [Exchange]);
CREATE INDEX [idx_ProductType] ON [dbo].[GeValidationRuns] ([ProductType]);
CREATE INDEX [idx_Exchange] ON [dbo].[GeValidationRuns] ([Exchange]);
CREATE INDEX [idx_Success] ON [dbo].[GeValidationRuns] ([Success]);
CREATE INDEX [idx_RegionTimestamp] ON [dbo].[GeValidationRuns] ([Region], [RunTimestamp]);
CREATE INDEX [idx_ExchangeTimestamp] ON [dbo].[GeValidationRuns] ([Exchange], [RunTimestamp]);
END
GO

-- ============================================================================
-- Individual expectation results table
-- Stores detailed results for each expectation in each validation run
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GeExpectationResults]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[GeExpectationResults] (
    [ResultId] BIGINT PRIMARY KEY IDENTITY(1,1),
    [RunId] BIGINT NOT NULL,
    
    -- Expectation details
    [ColumnName] NVARCHAR(255) NOT NULL,
    [ExpectationType] NVARCHAR(100) NOT NULL,
    [Success] BIT NOT NULL,
    
    -- Result metrics
    [ElementCount] INT NULL,
    [UnexpectedCount] INT NULL,
    [UnexpectedPercent] DECIMAL(5,2) NULL,
    [MissingCount] INT NULL,
    [MissingPercent] DECIMAL(5,2) NULL,
    
    -- Detailed result data (JSON for flexibility)
    [ResultDetails] NVARCHAR(MAX) NULL -- Stores partial_unexpected_list, partial_unexpected_counts, etc.
);

ALTER TABLE [dbo].[GeExpectationResults]
ADD CONSTRAINT [FK_GeExpectationResults_GeValidationRuns] 
FOREIGN KEY ([RunId]) REFERENCES [dbo].[GeValidationRuns]([RunId]) ON DELETE CASCADE;

CREATE INDEX [idx_RunId] ON [dbo].[GeExpectationResults] ([RunId]);
CREATE INDEX [idx_ColumnName] ON [dbo].[GeExpectationResults] ([ColumnName]);
CREATE INDEX [idx_ExpectationType] ON [dbo].[GeExpectationResults] ([ExpectationType]);
CREATE INDEX [idx_Success] ON [dbo].[GeExpectationResults] ([Success]);
CREATE INDEX [idx_ColumnExpectation] ON [dbo].[GeExpectationResults] ([ColumnName], [ExpectationType]);
CREATE INDEX [idx_RunSuccess] ON [dbo].[GeExpectationResults] ([RunId], [Success]);
END
GO

-- ============================================================================
-- Validation rules applied table
-- Tracks which specific rules were applied in each validation run
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GeValidationRulesApplied]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[GeValidationRulesApplied] (
    [RuleAppliedId] BIGINT PRIMARY KEY IDENTITY(1,1),
    [RunId] BIGINT NOT NULL,
    
    -- Rule identification
    [RuleName] NVARCHAR(255) NOT NULL,
    [RuleType] NVARCHAR(50) NOT NULL, -- base, product_type, exchange, custom, combined
    [RuleLevel] NVARCHAR(50) NULL, -- root, product_type, exchange
    
    -- Rule source
    [RuleSource] NVARCHAR(255) NULL -- File path or source of the rule
);

ALTER TABLE [dbo].[GeValidationRulesApplied]
ADD CONSTRAINT [FK_GeValidationRulesApplied_GeValidationRuns] 
FOREIGN KEY ([RunId]) REFERENCES [dbo].[GeValidationRuns]([RunId]) ON DELETE CASCADE;

CREATE INDEX [idx_RunId] ON [dbo].[GeValidationRulesApplied] ([RunId]);
CREATE INDEX [idx_RuleName] ON [dbo].[GeValidationRulesApplied] ([RuleName]);
CREATE INDEX [idx_RuleType] ON [dbo].[GeValidationRulesApplied] ([RuleType]);
CREATE INDEX [idx_RuleLevel] ON [dbo].[GeValidationRulesApplied] ([RuleLevel]);
CREATE INDEX [idx_RunRuleType] ON [dbo].[GeValidationRulesApplied] ([RunId], [RuleType]);
END
GO

-- ============================================================================
-- Validation summary table (denormalized for quick queries)
-- Pre-aggregated data for faster trend analysis
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GeValidationSummary]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[GeValidationSummary] (
    [SummaryId] BIGINT PRIMARY KEY IDENTITY(1,1),
    [RunTimestamp] DATETIME2 NOT NULL,
    [Region] NVARCHAR(50) NOT NULL,
    [ProductType] NVARCHAR(50) NOT NULL,
    [Exchange] NVARCHAR(50) NOT NULL,
    
    -- Aggregated metrics
    [TotalRuns] INT NOT NULL DEFAULT 1,
    [SuccessfulRuns] INT NOT NULL DEFAULT 0,
    [FailedRuns] INT NOT NULL DEFAULT 0,
    [AvgTotalExpectations] DECIMAL(10,2) NULL,
    [AvgFailedExpectations] DECIMAL(10,2) NULL,
    [AvgSuccessRate] DECIMAL(5,2) NULL, -- Percentage of successful expectations
    
    -- Time bucket for aggregation (hourly, daily, etc.)
    [TimeBucket] NVARCHAR(20) NOT NULL, -- Format: YYYY-MM-DD-HH for hourly, YYYY-MM-DD for daily
    [BucketType] NVARCHAR(20) NOT NULL -- hourly, daily, weekly, monthly
);

CREATE INDEX [idx_TimeBucket] ON [dbo].[GeValidationSummary] ([TimeBucket]);
CREATE INDEX [idx_RegionExchangeBucket] ON [dbo].[GeValidationSummary] ([Region], [Exchange], [TimeBucket]);
CREATE INDEX [idx_ExchangeBucket] ON [dbo].[GeValidationSummary] ([Exchange], [TimeBucket]);
CREATE INDEX [idx_BucketType] ON [dbo].[GeValidationSummary] ([BucketType]);
CREATE INDEX [idx_Timestamp] ON [dbo].[GeValidationSummary] ([RunTimestamp]);
END
GO

-- ============================================================================
-- Column-level trends table
-- Tracks trends for specific columns across time
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GeColumnTrends]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[GeColumnTrends] (
    [TrendId] BIGINT PRIMARY KEY IDENTITY(1,1),
    [RunTimestamp] DATETIME2 NOT NULL,
    [Exchange] NVARCHAR(50) NOT NULL,
    [ColumnName] NVARCHAR(255) NOT NULL,
    [ExpectationType] NVARCHAR(100) NOT NULL,
    
    -- Trend metrics
    [SuccessRate] DECIMAL(5,2) NOT NULL, -- Percentage of times this expectation passed
    [FailureCount] INT NOT NULL DEFAULT 0,
    [TotalOccurrences] INT NOT NULL DEFAULT 1,
    
    -- Time bucket
    [TimeBucket] NVARCHAR(20) NOT NULL,
    [BucketType] NVARCHAR(20) NOT NULL
);

CREATE INDEX [idx_ExchangeColumn] ON [dbo].[GeColumnTrends] ([Exchange], [ColumnName]);
CREATE INDEX [idx_ColumnExpectation] ON [dbo].[GeColumnTrends] ([ColumnName], [ExpectationType]);
CREATE INDEX [idx_TimeBucket] ON [dbo].[GeColumnTrends] ([TimeBucket]);
CREATE INDEX [idx_ExchangeBucket] ON [dbo].[GeColumnTrends] ([Exchange], [TimeBucket]);
END
GO

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- View: Latest validation results per exchange
IF OBJECT_ID('[dbo].[v_latest_validations]', 'V') IS NOT NULL
    DROP VIEW [dbo].[v_latest_validations];
GO

CREATE VIEW [dbo].[v_latest_validations] AS
SELECT 
    vr.*,
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success] as [ExpectationSuccess],
    er.[UnexpectedCount],
    er.[UnexpectedPercent]
FROM [dbo].[GeValidationRuns] vr
LEFT JOIN [dbo].[GeExpectationResults] er ON vr.[RunId] = er.[RunId]
WHERE vr.[RunTimestamp] >= DATEADD(DAY, -1, GETDATE());
GO

-- View: Exchange success rates over time
IF OBJECT_ID('[dbo].[v_exchange_success_rates]', 'V') IS NOT NULL
    DROP VIEW [dbo].[v_exchange_success_rates];
GO

CREATE VIEW [dbo].[v_exchange_success_rates] AS
SELECT 
    [Exchange],
    CAST([RunTimestamp] AS DATE) as [ValidationDate],
    COUNT(*) as [TotalRuns],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulRuns],
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) as [FailedRuns],
    AVG([FailedExpectations]) as [AvgFailedExpectations],
    AVG([TotalExpectations]) as [AvgTotalExpectations],
    (SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent]
FROM [dbo].[GeValidationRuns]
GROUP BY [Exchange], CAST([RunTimestamp] AS DATE);
GO

-- View: Column failure trends
IF OBJECT_ID('[dbo].[v_column_failure_trends]', 'V') IS NOT NULL
    DROP VIEW [dbo].[v_column_failure_trends];
GO

CREATE VIEW [dbo].[v_column_failure_trends] AS
SELECT 
    er.[ColumnName],
    er.[ExpectationType],
    CAST(vr.[RunTimestamp] AS DATE) as [ValidationDate],
    COUNT(*) as [TotalChecks],
    SUM(CASE WHEN er.[Success] = 0 THEN 1 ELSE 0 END) as [FailureCount],
    AVG(er.[UnexpectedPercent]) as [AvgUnexpectedPercent],
    (SUM(CASE WHEN er.[Success] = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [FailureRatePercent]
FROM [dbo].[GeExpectationResults] er
JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE er.[Success] = 0
GROUP BY er.[ColumnName], er.[ExpectationType], CAST(vr.[RunTimestamp] AS DATE);
GO

-- View: Rule effectiveness analysis
IF OBJECT_ID('[dbo].[v_rule_effectiveness]', 'V') IS NOT NULL
    DROP VIEW [dbo].[v_rule_effectiveness];
GO

CREATE VIEW [dbo].[v_rule_effectiveness] AS
SELECT 
    vra.[RuleName],
    vra.[RuleType],
    vra.[RuleLevel],
    COUNT(DISTINCT vra.[RunId]) as [TimesApplied],
    SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulValidations],
    SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) as [FailedValidations],
    AVG(vr.[FailedExpectations]) as [AvgFailedExpectations],
    (SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT vra.[RunId])) as [SuccessRatePercent]
FROM [dbo].[GeValidationRulesApplied] vra
JOIN [dbo].[GeValidationRuns] vr ON vra.[RunId] = vr.[RunId]
GROUP BY vra.[RuleName], vra.[RuleType], vra.[RuleLevel];
GO
