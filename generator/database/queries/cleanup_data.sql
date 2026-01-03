-- ============================================
-- Cleanup Script for Validation Data
-- ============================================
-- WARNING: This script will DELETE data from the database
-- Review carefully before executing
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- 1. Preview Data Before Deletion
-- ============================================
PRINT '============================================';
PRINT 'PREVIEW: Current Data Counts';
PRINT '============================================';

SELECT 'GeValidationRuns' AS TableName, COUNT(*) AS RecordCount FROM [dbo].[GeValidationRuns]
UNION ALL
SELECT 'GeExpectationResults', COUNT(*) FROM [dbo].[GeExpectationResults]
UNION ALL
SELECT 'GeValidationRulesApplied', COUNT(*) FROM [dbo].[GeValidationRulesApplied];
GO

-- Show date range of data
SELECT 
    MIN([RunTimestamp]) AS OldestRecord,
    MAX([RunTimestamp]) AS NewestRecord,
    COUNT(*) AS TotalRuns
FROM [dbo].[GeValidationRuns];
GO

-- ============================================
-- 2. DELETE ALL DATA (Uncomment to use)
-- ============================================
-- WARNING: This will delete ALL validation data
-- Uncomment the lines below to execute

/*
PRINT '============================================';
PRINT 'DELETING ALL VALIDATION DATA';
PRINT '============================================';

-- Delete in order to respect foreign key constraints
DELETE FROM [dbo].[GeExpectationResults];
PRINT 'Deleted all GeExpectationResults';

DELETE FROM [dbo].[GeValidationRulesApplied];
PRINT 'Deleted all GeValidationRulesApplied';

DELETE FROM [dbo].[GeValidationRuns];
PRINT 'Deleted all GeValidationRuns';

PRINT '============================================';
PRINT 'Cleanup Complete - All data deleted';
PRINT '============================================';
GO
*/

-- ============================================
-- 3. DELETE DATA BY DATE RANGE
-- ============================================
-- Delete data older than a specific date
-- Modify the date as needed

/*
DECLARE @CutoffDate DATETIME2 = '2025-01-01'; -- Change this date
DECLARE @DeletedRuns INT;
DECLARE @DeletedExpectations INT;
DECLARE @DeletedRules INT;

PRINT '============================================';
PRINT 'DELETING DATA OLDER THAN: ' + CAST(@CutoffDate AS VARCHAR(50));
PRINT '============================================';

-- Get RunIds to delete
DECLARE @RunIdsToDelete TABLE (RunId INT);
INSERT INTO @RunIdsToDelete
SELECT [RunId] FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] < @CutoffDate;

-- Delete related records first
DELETE er FROM [dbo].[GeExpectationResults] er
INNER JOIN @RunIdsToDelete r ON er.[RunId] = r.RunId;
SET @DeletedExpectations = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedExpectations AS VARCHAR(10)) + ' expectation results';

DELETE ra FROM [dbo].[GeValidationRulesApplied] ra
INNER JOIN @RunIdsToDelete r ON ra.[RunId] = r.RunId;
SET @DeletedRules = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRules AS VARCHAR(10)) + ' rules applied';

-- Delete main records
DELETE vr FROM [dbo].[GeValidationRuns] vr
INNER JOIN @RunIdsToDelete r ON vr.[RunId] = r.RunId;
SET @DeletedRuns = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRuns AS VARCHAR(10)) + ' validation runs';

PRINT '============================================';
PRINT 'Cleanup Complete';
PRINT '============================================';
GO
*/

-- ============================================
-- 4. DELETE DATA BY REGION/EXCHANGE
-- ============================================
-- Delete data for specific region and/or exchange
-- Modify the WHERE clause as needed

/*
DECLARE @Region NVARCHAR(50) = 'apac'; -- Change or set to NULL for all regions
DECLARE @Exchange NVARCHAR(50) = 'XHKG'; -- Change or set to NULL for all exchanges
DECLARE @DeletedRuns INT;
DECLARE @DeletedExpectations INT;
DECLARE @DeletedRules INT;

PRINT '============================================';
PRINT 'DELETING DATA FOR:';
IF @Region IS NOT NULL PRINT '  Region: ' + @Region;
IF @Exchange IS NOT NULL PRINT '  Exchange: ' + @Exchange;
PRINT '============================================';

-- Get RunIds to delete
DECLARE @RunIdsToDelete TABLE (RunId INT);
INSERT INTO @RunIdsToDelete
SELECT [RunId] FROM [dbo].[GeValidationRuns]
WHERE (@Region IS NULL OR [Region] = @Region)
  AND (@Exchange IS NULL OR [Exchange] = @Exchange);

-- Delete related records first
DELETE er FROM [dbo].[GeExpectationResults] er
INNER JOIN @RunIdsToDelete r ON er.[RunId] = r.RunId;
SET @DeletedExpectations = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedExpectations AS VARCHAR(10)) + ' expectation results';

DELETE ra FROM [dbo].[GeValidationRulesApplied] ra
INNER JOIN @RunIdsToDelete r ON ra.[RunId] = r.RunId;
SET @DeletedRules = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRules AS VARCHAR(10)) + ' rules applied';

-- Delete main records
DELETE vr FROM [dbo].[GeValidationRuns] vr
INNER JOIN @RunIdsToDelete r ON vr.[RunId] = r.RunId;
SET @DeletedRuns = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRuns AS VARCHAR(10)) + ' validation runs';

PRINT '============================================';
PRINT 'Cleanup Complete';
PRINT '============================================';
GO
*/

-- ============================================
-- 5. DELETE DATA BY RUN ID RANGE
-- ============================================
-- Delete specific RunIds or a range

/*
DECLARE @MinRunId INT = 1; -- Change as needed
DECLARE @MaxRunId INT = 100; -- Change as needed
DECLARE @DeletedRuns INT;
DECLARE @DeletedExpectations INT;
DECLARE @DeletedRules INT;

PRINT '============================================';
PRINT 'DELETING DATA FOR RunIds: ' + CAST(@MinRunId AS VARCHAR(10)) + ' TO ' + CAST(@MaxRunId AS VARCHAR(10));
PRINT '============================================';

-- Get RunIds to delete
DECLARE @RunIdsToDelete TABLE (RunId INT);
INSERT INTO @RunIdsToDelete
SELECT [RunId] FROM [dbo].[GeValidationRuns]
WHERE [RunId] >= @MinRunId AND [RunId] <= @MaxRunId;

-- Delete related records first
DELETE er FROM [dbo].[GeExpectationResults] er
INNER JOIN @RunIdsToDelete r ON er.[RunId] = r.RunId;
SET @DeletedExpectations = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedExpectations AS VARCHAR(10)) + ' expectation results';

DELETE ra FROM [dbo].[GeValidationRulesApplied] ra
INNER JOIN @RunIdsToDelete r ON ra.[RunId] = r.RunId;
SET @DeletedRules = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRules AS VARCHAR(10)) + ' rules applied';

-- Delete main records
DELETE vr FROM [dbo].[GeValidationRuns] vr
INNER JOIN @RunIdsToDelete r ON vr.[RunId] = r.RunId;
SET @DeletedRuns = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRuns AS VARCHAR(10)) + ' validation runs';

PRINT '============================================';
PRINT 'Cleanup Complete';
PRINT '============================================';
GO
*/

-- ============================================
-- 6. DELETE OLD DATA (Keep Last N Days)
-- ============================================
-- Keep only the last N days of data

/*
DECLARE @DaysToKeep INT = 30; -- Keep last 30 days
DECLARE @CutoffDate DATETIME2 = DATEADD(DAY, -@DaysToKeep, GETDATE());
DECLARE @DeletedRuns INT;
DECLARE @DeletedExpectations INT;
DECLARE @DeletedRules INT;

PRINT '============================================';
PRINT 'KEEPING LAST ' + CAST(@DaysToKeep AS VARCHAR(10)) + ' DAYS';
PRINT 'DELETING DATA OLDER THAN: ' + CAST(@CutoffDate AS VARCHAR(50));
PRINT '============================================';

-- Get RunIds to delete
DECLARE @RunIdsToDelete TABLE (RunId INT);
INSERT INTO @RunIdsToDelete
SELECT [RunId] FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] < @CutoffDate;

-- Delete related records first
DELETE er FROM [dbo].[GeExpectationResults] er
INNER JOIN @RunIdsToDelete r ON er.[RunId] = r.RunId;
SET @DeletedExpectations = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedExpectations AS VARCHAR(10)) + ' expectation results';

DELETE ra FROM [dbo].[GeValidationRulesApplied] ra
INNER JOIN @RunIdsToDelete r ON ra.[RunId] = r.RunId;
SET @DeletedRules = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRules AS VARCHAR(10)) + ' rules applied';

-- Delete main records
DELETE vr FROM [dbo].[GeValidationRuns] vr
INNER JOIN @RunIdsToDelete r ON vr.[RunId] = r.RunId;
SET @DeletedRuns = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRuns AS VARCHAR(10)) + ' validation runs';

PRINT '============================================';
PRINT 'Cleanup Complete';
PRINT '============================================';
GO
*/

-- ============================================
-- 7. RESET IDENTITY COUNTERS (Optional)
-- ============================================
-- After deleting all data, you may want to reset identity counters
-- Uncomment to use

/*
DBCC CHECKIDENT ('[dbo].[GeValidationRuns]', RESEED, 0);
PRINT 'Reset GeValidationRuns identity counter to 0';

DBCC CHECKIDENT ('[dbo].[GeExpectationResults]', RESEED, 0);
PRINT 'Reset GeExpectationResults identity counter to 0';

DBCC CHECKIDENT ('[dbo].[GeValidationRulesApplied]', RESEED, 0);
PRINT 'Reset GeValidationRulesApplied identity counter to 0';
GO
*/

-- ============================================
-- 8. VERIFY CLEANUP
-- ============================================
-- Run this after cleanup to verify

PRINT '============================================';
PRINT 'VERIFICATION: Remaining Data Counts';
PRINT '============================================';

SELECT 'GeValidationRuns' AS TableName, COUNT(*) AS RecordCount FROM [dbo].[GeValidationRuns]
UNION ALL
SELECT 'GeExpectationResults', COUNT(*) FROM [dbo].[GeExpectationResults]
UNION ALL
SELECT 'GeValidationRulesApplied', COUNT(*) FROM [dbo].[GeValidationRulesApplied];
GO



