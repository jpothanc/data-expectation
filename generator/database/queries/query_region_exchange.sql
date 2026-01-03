-- ============================================
-- Query Validation Results by Region and Exchange
-- ============================================
-- Get all validation results for a specific region and exchange
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- 1. Basic Query: Get Validation Runs for Region and Exchange
-- ============================================
-- Replace @Region and @Exchange with your values

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    vr.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    vr.[Success],
    vr.[TotalExpectations],
    vr.[SuccessfulExpectations],
    vr.[FailedExpectations],
    vr.[RulesApplied],
    vr.[CustomRuleNames],
    vr.[ApiUrl],
    vr.[ExecutionDurationMs]
FROM [dbo].[GeValidationRuns] vr
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY vr.[RunTimestamp] DESC;
GO

-- ============================================
-- 2. Complete Results: Runs with Expectation Results
-- ============================================
-- Get all runs with their expectation results

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    vr.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    vr.[Success],
    vr.[TotalExpectations],
    vr.[SuccessfulExpectations],
    vr.[FailedExpectations],
    er.[ResultId],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success] AS ExpectationSuccess,
    er.[ElementCount],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    er.[MissingCount],
    er.[MissingPercent],
    er.[ResultDetails]
FROM [dbo].[GeValidationRuns] vr
LEFT JOIN [dbo].[GeExpectationResults] er ON vr.[RunId] = er.[RunId]
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY vr.[RunTimestamp] DESC, er.[ColumnName], er.[ExpectationType];
GO

-- ============================================
-- 3. Summary Statistics by Region and Exchange
-- ============================================

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    vr.[Region],
    vr.[Exchange],
    vr.[ProductType],
    COUNT(*) AS TotalRuns,
    SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) AS SuccessfulRuns,
    SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) AS FailedRuns,
    AVG(CAST(vr.[SuccessfulExpectations] AS FLOAT) / NULLIF(vr.[TotalExpectations], 0) * 100.0) AS AvgSuccessRate,
    AVG(CAST(vr.[ExecutionDurationMs] AS FLOAT)) AS AvgExecutionDurationMs,
    MIN(vr.[RunTimestamp]) AS FirstRun,
    MAX(vr.[RunTimestamp]) AS LastRun
FROM [dbo].[GeValidationRuns] vr
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
GROUP BY vr.[Region], vr.[Exchange], vr.[ProductType]
ORDER BY vr.[ProductType];
GO

-- ============================================
-- 4. Failed Expectations with Details
-- ============================================
-- Get all failed expectations with unexpected values

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    vr.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    er.[MissingCount],
    er.[MissingPercent],
    er.[ResultDetails],
    -- Extract partial_unexpected_counts from JSON
    JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') AS PartialUnexpectedCounts
FROM [dbo].[GeValidationRuns] vr
INNER JOIN [dbo].[GeExpectationResults] er ON vr.[RunId] = er.[RunId]
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND er.[Success] = 0
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY vr.[RunTimestamp] DESC, er.[UnexpectedPercent] DESC;
GO

-- ============================================
-- 5. Expand Unexpected Values
-- ============================================
-- Expand partial_unexpected_counts into individual rows

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    vr.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    unexpected_value.[value] AS UnexpectedValue,
    unexpected_value.[count] AS ValueCount,
    er.[UnexpectedCount],
    er.[UnexpectedPercent]
FROM [dbo].[GeValidationRuns] vr
INNER JOIN [dbo].[GeExpectationResults] er ON vr.[RunId] = er.[RunId]
CROSS APPLY OPENJSON(JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts'))
    WITH (
        [value] NVARCHAR(MAX) '$.value',
        [count] INT '$.count'
    ) AS unexpected_value
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND er.[Success] = 0
  AND er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != 'null'
  AND JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY vr.[RunTimestamp] DESC, er.[ColumnName], unexpected_value.[count] DESC;
GO

-- ============================================
-- 6. Rules Applied for Region and Exchange
-- ============================================

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    vr.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    vra.[RuleName],
    vra.[RuleType],
    vra.[RuleLevel],
    vra.[RuleSource]
FROM [dbo].[GeValidationRuns] vr
INNER JOIN [dbo].[GeValidationRulesApplied] vra ON vr.[RunId] = vra.[RunId]
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY vr.[RunTimestamp] DESC, vra.[RuleType], vra.[RuleLevel];
GO

-- ============================================
-- 7. Complete Data Export (All Tables Joined)
-- ============================================
-- Get everything in one query for export/analysis

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    -- Run information
    vr.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    vr.[Success] AS RunSuccess,
    vr.[TotalExpectations],
    vr.[SuccessfulExpectations],
    vr.[FailedExpectations],
    vr.[RulesApplied],
    vr.[CustomRuleNames],
    vr.[ApiUrl],
    vr.[ExecutionDurationMs],
    -- Expectation information
    er.[ResultId],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success] AS ExpectationSuccess,
    er.[ElementCount],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    er.[MissingCount],
    er.[MissingPercent],
    er.[ResultDetails],
    -- Rule information
    vra.[RuleName],
    vra.[RuleType],
    vra.[RuleLevel],
    vra.[RuleSource]
FROM [dbo].[GeValidationRuns] vr
LEFT JOIN [dbo].[GeExpectationResults] er ON vr.[RunId] = er.[RunId]
LEFT JOIN [dbo].[GeValidationRulesApplied] vra ON vr.[RunId] = vra.[RunId]
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY vr.[RunTimestamp] DESC, er.[ColumnName], er.[ExpectationType], vra.[RuleType];
GO

-- ============================================
-- 8. Trend Analysis: Success Rate Over Time
-- ============================================
-- Group by date to see trends

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    CAST(vr.[RunTimestamp] AS DATE) AS RunDate,
    vr.[ProductType],
    COUNT(*) AS TotalRuns,
    SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) AS SuccessfulRuns,
    SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) AS FailedRuns,
    CAST(SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS SuccessRate,
    AVG(CAST(vr.[SuccessfulExpectations] AS FLOAT) / NULLIF(vr.[TotalExpectations], 0) * 100.0) AS AvgExpectationSuccessRate
FROM [dbo].[GeValidationRuns] vr
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
GROUP BY CAST(vr.[RunTimestamp] AS DATE), vr.[ProductType]
ORDER BY RunDate DESC, vr.[ProductType];
GO

-- ============================================
-- 9. Most Common Failure Reasons
-- ============================================
-- Identify patterns in failures

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this
DECLARE @Days INT = 30; -- Optional: number of days to look back

SELECT 
    er.[ColumnName],
    er.[ExpectationType],
    COUNT(*) AS FailureCount,
    AVG(er.[UnexpectedPercent]) AS AvgUnexpectedPercent,
    AVG(er.[MissingPercent]) AS AvgMissingPercent
FROM [dbo].[GeValidationRuns] vr
INNER JOIN [dbo].[GeExpectationResults] er ON vr.[RunId] = er.[RunId]
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
  AND er.[Success] = 0
  AND vr.[RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
GROUP BY er.[ColumnName], er.[ExpectationType]
ORDER BY FailureCount DESC;
GO

-- ============================================
-- 10. Quick Check: Latest Run Details
-- ============================================
-- Get the most recent run for region and exchange

DECLARE @Region NVARCHAR(50) = 'apac'; -- Change this
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change this

SELECT TOP 1
    vr.*,
    (SELECT COUNT(*) FROM [dbo].[GeExpectationResults] WHERE [RunId] = vr.[RunId]) AS ExpectationCount,
    (SELECT COUNT(*) FROM [dbo].[GeValidationRulesApplied] WHERE [RunId] = vr.[RunId]) AS RulesCount
FROM [dbo].[GeValidationRuns] vr
WHERE vr.[Region] = @Region
  AND vr.[Exchange] = @Exchange
ORDER BY vr.[RunTimestamp] DESC;
GO



