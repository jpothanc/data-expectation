-- ============================================
-- Diagnostic Query for Treemap Data Issues
-- ============================================
-- Use this to diagnose why treemap shows incorrect values
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- 1. Check XHKG Data Directly
-- ============================================
DECLARE @Days INT = 7;

SELECT 
    [RunId],
    [RunTimestamp],
    [Region],
    [ProductType],
    [Exchange],
    [Success],
    [TotalExpectations],
    [SuccessfulExpectations],
    [FailedExpectations],
    -- Calculate success rate
    CAST([SuccessfulExpectations] * 100.0 / NULLIF([TotalExpectations], 0) AS DECIMAL(5,2)) AS ExpectationSuccessRate
FROM [dbo].[GeValidationRuns]
WHERE [Exchange] = 'XHKG'
  AND [RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
ORDER BY [RunTimestamp] DESC;
GO

-- ============================================
-- 2. Check Treemap Calculation for XHKG
-- ============================================
DECLARE @Days INT = 7;

SELECT 
    [Region],
    [ProductType],
    [Exchange],
    COUNT(*) as [TotalRuns],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) AS SuccessfulRuns,
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) AS FailedRuns,
    SUM([TotalExpectations]) AS TotalExpectationsSum,
    SUM([SuccessfulExpectations]) AS SuccessfulExpectationsSum,
    SUM([FailedExpectations]) AS FailedExpectationsSum,
    -- Run-level success rate
    CAST(SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS RunSuccessRate,
    -- Expectation-level success rate (more accurate)
    CAST(
        CASE 
            WHEN SUM([TotalExpectations]) > 0 
            THEN SUM([SuccessfulExpectations]) * 100.0 / SUM([TotalExpectations])
            ELSE 0 
        END 
        AS DECIMAL(5,2)
    ) AS ExpectationSuccessRate
FROM [dbo].[GeValidationRuns]
WHERE [Exchange] = 'XHKG'
  AND [RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
GROUP BY [Region], [ProductType], [Exchange];
GO

-- ============================================
-- 3. Check All Exchanges for Comparison
-- ============================================
DECLARE @Days INT = 7;

SELECT 
    [Exchange],
    COUNT(*) as [TotalRuns],
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) AS SuccessfulRuns,
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) AS FailedRuns,
    CAST(
        CASE 
            WHEN SUM([TotalExpectations]) > 0 
            THEN SUM([SuccessfulExpectations]) * 100.0 / SUM([TotalExpectations])
            ELSE 0 
        END 
        AS DECIMAL(5,2)
    ) AS SuccessRate
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
GROUP BY [Exchange]
ORDER BY [Exchange];
GO

-- ============================================
-- 4. Check Data Types and NULL Values
-- ============================================
DECLARE @Days INT = 7;

SELECT 
    [Exchange],
    COUNT(*) AS TotalRecords,
    SUM(CASE WHEN [Success] IS NULL THEN 1 ELSE 0 END) AS NullSuccess,
    SUM(CASE WHEN [TotalExpectations] IS NULL OR [TotalExpectations] = 0 THEN 1 ELSE 0 END) AS InvalidTotalExpectations,
    SUM(CASE WHEN [SuccessfulExpectations] IS NULL THEN 1 ELSE 0 END) AS NullSuccessfulExpectations,
    MIN([Success]) AS MinSuccess,
    MAX([Success]) AS MaxSuccess,
    MIN([TotalExpectations]) AS MinTotalExpectations,
    MAX([TotalExpectations]) AS MaxTotalExpectations
FROM [dbo].[GeValidationRuns]
WHERE [Exchange] = 'XHKG'
  AND [RunTimestamp] >= DATEADD(DAY, -@Days, GETDATE())
GROUP BY [Exchange];
GO



