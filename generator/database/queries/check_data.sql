-- ============================================
-- Queries to Check Validation Data in Database
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- 1. Check Recent Validation Runs
-- ============================================
SELECT TOP 20
    [RunId],
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
FROM [dbo].[GeValidationRuns]
ORDER BY [RunTimestamp] DESC;
GO

-- ============================================
-- 2. Count Records by Table
-- ============================================
SELECT 'GeValidationRuns' AS TableName, COUNT(*) AS RecordCount FROM [dbo].[GeValidationRuns]
UNION ALL
SELECT 'GeExpectationResults', COUNT(*) FROM [dbo].[GeExpectationResults]
UNION ALL
SELECT 'GeValidationRulesApplied', COUNT(*) FROM [dbo].[GeValidationRulesApplied];
GO

-- ============================================
-- 3. Check Latest Run Details
-- ============================================
DECLARE @LatestRunId INT;
SELECT @LatestRunId = MAX([RunId]) FROM [dbo].[GeValidationRuns];

IF @LatestRunId IS NOT NULL
BEGIN
    PRINT 'Latest RunId: ' + CAST(@LatestRunId AS VARCHAR(10));
    
    -- Main run record
    SELECT * FROM [dbo].[GeValidationRuns] WHERE [RunId] = @LatestRunId;
    
    -- Expectation results for latest run
    SELECT 
        [RunId],
        [ColumnName],
        [ExpectationType],
        [Success],
        [ElementCount],
        [UnexpectedCount],
        [UnexpectedPercent],
        [MissingCount],
        [MissingPercent]
    FROM [dbo].[GeExpectationResults]
    WHERE [RunId] = @LatestRunId
    ORDER BY [ColumnName], [ExpectationType];
    
    -- Rules applied for latest run
    SELECT 
        [RunId],
        [RuleName],
        [RuleType],
        [RuleLevel],
        [RuleSource]
    FROM [dbo].[GeValidationRulesApplied]
    WHERE [RunId] = @LatestRunId
    ORDER BY [RuleType], [RuleLevel];
END
ELSE
BEGIN
    PRINT 'No records found in GeValidationRuns table';
END
GO

-- ============================================
-- 4. Check Data by Region/Exchange
-- ============================================
SELECT 
    [Region],
    [ProductType],
    [Exchange],
    COUNT(*) AS RunCount,
    SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) AS SuccessfulRuns,
    SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) AS FailedRuns,
    MAX([RunTimestamp]) AS LastRunTime
FROM [dbo].[GeValidationRuns]
GROUP BY [Region], [ProductType], [Exchange]
ORDER BY [Region], [ProductType], [Exchange];
GO

-- ============================================
-- 5. Check Failed Expectations
-- ============================================
SELECT TOP 50
    er.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success],
    er.[UnexpectedCount],
    er.[UnexpectedPercent]
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE er.[Success] = 0
ORDER BY vr.[RunTimestamp] DESC, er.[UnexpectedPercent] DESC;
GO

-- ============================================
-- 6. Verify Database Name
-- ============================================
SELECT DB_NAME() AS CurrentDatabase;
GO

-- ============================================
-- 7. Check Table Existence and Row Counts
-- ============================================
IF OBJECT_ID('[dbo].[GeValidationRuns]', 'U') IS NOT NULL
    SELECT 'GeValidationRuns EXISTS' AS Status, COUNT(*) AS RowCount FROM [dbo].[GeValidationRuns]
ELSE
    SELECT 'GeValidationRuns DOES NOT EXIST' AS Status, 0 AS RowCount;

IF OBJECT_ID('[dbo].[GeExpectationResults]', 'U') IS NOT NULL
    SELECT 'GeExpectationResults EXISTS' AS Status, COUNT(*) AS RowCount FROM [dbo].[GeExpectationResults]
ELSE
    SELECT 'GeExpectationResults DOES NOT EXIST' AS Status, 0 AS RowCount;

IF OBJECT_ID('[dbo].[GeValidationRulesApplied]', 'U') IS NOT NULL
    SELECT 'GeValidationRulesApplied EXISTS' AS Status, COUNT(*) AS RowCount FROM [dbo].[GeValidationRulesApplied]
ELSE
    SELECT 'GeValidationRulesApplied DOES NOT EXIST' AS Status, 0 AS RowCount;
GO



