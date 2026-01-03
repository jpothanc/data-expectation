-- Analytics and trending queries for validation results
-- These queries support chart generation and trend analysis
-- SQL Server compatible syntax

-- Use RubyUsers database
USE [RubyUsers];
GO

-- ============================================================================
-- 1. Success Rate Trends Over Time (for line charts)
-- ============================================================================
SELECT 
    FORMAT([RunTimestamp], 'yyyy-MM-dd HH:00:00') as [TimeBucket],
    [Exchange],
    COUNT(*) as [TotalRuns],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulRuns],
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) as [FailedRuns],
    (SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent],
    AVG([FailedExpectations]) as [AvgFailedExpectations]
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] >= DATEADD(DAY, -7, GETDATE())
GROUP BY FORMAT([RunTimestamp], 'yyyy-MM-dd HH:00:00'), [Exchange]
ORDER BY [TimeBucket], [Exchange];

-- ============================================================================
-- 2. Exchange Comparison (for bar charts)
-- ============================================================================
SELECT 
    [Exchange],
    COUNT(*) as [TotalValidations],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulValidations],
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) as [FailedValidations],
    AVG([TotalExpectations]) as [AvgTotalExpectations],
    AVG([FailedExpectations]) as [AvgFailedExpectations],
    (SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent]
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] >= DATEADD(DAY, -1, GETDATE())
GROUP BY [Exchange]
ORDER BY [SuccessRatePercent] DESC;

-- ============================================================================
-- 3. Column Failure Analysis (for pie/bar charts)
-- ============================================================================
SELECT TOP 20
    er.[ColumnName],
    er.[ExpectationType],
    COUNT(*) as [TotalChecks],
    SUM(CASE WHEN er.[Success] = 0 THEN 1 ELSE 0 END) as [FailureCount],
    AVG(er.[UnexpectedPercent]) as [AvgUnexpectedPercent],
    (SUM(CASE WHEN er.[Success] = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [FailureRatePercent]
FROM [dbo].[GeExpectationResults] er
JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE vr.[RunTimestamp] >= DATEADD(DAY, -7, GETDATE())
GROUP BY er.[ColumnName], er.[ExpectationType]
HAVING SUM(CASE WHEN er.[Success] = 0 THEN 1 ELSE 0 END) > 0
ORDER BY [FailureCount] DESC;

-- ============================================================================
-- 4. Rule Effectiveness Analysis
-- ============================================================================
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
WHERE vr.[RunTimestamp] >= DATEADD(DAY, -30, GETDATE())
GROUP BY vra.[RuleName], vra.[RuleType], vra.[RuleLevel]
ORDER BY [TimesApplied] DESC;

-- ============================================================================
-- 5. Custom Rules Performance
-- ============================================================================
SELECT 
    vr.[CustomRuleNames],
    COUNT(*) as [TotalRuns],
    SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulRuns],
    SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) as [FailedRuns],
    AVG(vr.[FailedExpectations]) as [AvgFailedExpectations],
    (SUM(CASE WHEN vr.[Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent]
FROM [dbo].[GeValidationRuns] vr
WHERE vr.[CustomRuleNames] IS NOT NULL
  AND vr.[RunTimestamp] >= DATEADD(DAY, -30, GETDATE())
GROUP BY vr.[CustomRuleNames]
ORDER BY [TotalRuns] DESC;

-- ============================================================================
-- 6. Regional Trends
-- ============================================================================
SELECT 
    [Region],
    [Exchange],
    CAST([RunTimestamp] AS DATE) as [ValidationDate],
    COUNT(*) as [TotalRuns],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulRuns],
    AVG([FailedExpectations]) as [AvgFailedExpectations],
    (SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent]
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] >= DATEADD(DAY, -30, GETDATE())
GROUP BY [Region], [Exchange], CAST([RunTimestamp] AS DATE)
ORDER BY [ValidationDate] DESC, [Region], [Exchange];

-- ============================================================================
-- 7. Most Common Failures (for alerts/dashboards)
-- ============================================================================
SELECT TOP 50
    er.[ColumnName],
    er.[ExpectationType],
    vr.[Exchange],
    COUNT(*) as [FailureCount],
    AVG(er.[UnexpectedPercent]) as [AvgUnexpectedPercent],
    MAX(vr.[RunTimestamp]) as [LastOccurrence]
FROM [dbo].[GeExpectationResults] er
JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE er.[Success] = 0
  AND vr.[RunTimestamp] >= DATEADD(DAY, -7, GETDATE())
GROUP BY er.[ColumnName], er.[ExpectationType], vr.[Exchange]
ORDER BY [FailureCount] DESC;

-- ============================================================================
-- 8. Hourly Aggregation for Time Series Charts
-- ============================================================================
SELECT 
    FORMAT([RunTimestamp], 'yyyy-MM-dd HH:00:00') as [HourBucket],
    [Exchange],
    COUNT(*) as [ValidationCount],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessCount],
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) as [FailureCount],
    AVG([TotalExpectations]) as [AvgTotalExpectations],
    AVG([FailedExpectations]) as [AvgFailedExpectations],
    (SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent]
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] >= DATEADD(DAY, -7, GETDATE())
GROUP BY FORMAT([RunTimestamp], 'yyyy-MM-dd HH:00:00'), [Exchange]
ORDER BY [HourBucket], [Exchange];

-- ============================================================================
-- 9. Product Type Comparison
-- ============================================================================
SELECT 
    [ProductType],
    COUNT(*) as [TotalValidations],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulValidations],
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) as [FailedValidations],
    AVG([TotalExpectations]) as [AvgTotalExpectations],
    AVG([FailedExpectations]) as [AvgFailedExpectations],
    (SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as [SuccessRatePercent]
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] >= DATEADD(DAY, -30, GETDATE())
GROUP BY [ProductType]
ORDER BY [SuccessRatePercent] DESC;

-- ============================================================================
-- 10. Detailed Failure Breakdown by Exchange and Column
-- ============================================================================
SELECT 
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    COUNT(*) as [FailureCount],
    AVG(er.[UnexpectedCount]) as [AvgUnexpectedCount],
    AVG(er.[UnexpectedPercent]) as [AvgUnexpectedPercent],
    MAX(vr.[RunTimestamp]) as [LastFailureTime]
FROM [dbo].[GeExpectationResults] er
JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE er.[Success] = 0
  AND vr.[RunTimestamp] >= DATEADD(DAY, -7, GETDATE())
GROUP BY vr.[Exchange], er.[ColumnName], er.[ExpectationType]
ORDER BY [FailureCount] DESC;
