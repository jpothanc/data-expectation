-- Quick check queries for validation data
-- Run these in SQL Server Management Studio or Azure Data Studio

USE [RubyUsers];
GO

-- 1. Check if any data exists
SELECT COUNT(*) AS TotalRuns FROM [dbo].[GeValidationRuns];
SELECT COUNT(*) AS TotalExpectations FROM [dbo].[GeExpectationResults];
SELECT COUNT(*) AS TotalRules FROM [dbo].[GeValidationRulesApplied];
GO

-- 2. Show latest 5 runs
SELECT TOP 5
    [RunId],
    [RunTimestamp],
    [Region],
    [ProductType],
    [Exchange],
    [Success],
    [TotalExpectations],
    [FailedExpectations]
FROM [dbo].[GeValidationRuns]
ORDER BY [RunTimestamp] DESC;
GO

-- 3. Check what database you're connected to
SELECT DB_NAME() AS CurrentDatabase;
GO



